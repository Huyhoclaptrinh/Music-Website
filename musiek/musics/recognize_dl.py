"""
Deep Learning Sound Recognition Service for Django and CLI.

Provides `recognize_audio_dl(file_path)`:
- Loads (and caches) the AudioEncoder neural model.
- Loads (and caches) the MusicIndex database vector index.
- Automatically handles query slicing, embedding extraction, and temporal offset voting.
- Returns matched song metadata or "Unknown Song".
"""

import os
from typing import Optional, Tuple, Dict, Any
import torch
try:
    from django.conf import settings
except ImportError:
    settings = None

from .audio_encoder import AudioEncoder, AudioEncoderConfig, load_audio
from .matcher import MusicIndex, MatchResult


class SoundRecognizerService:
    """Singleton service maintaining cached AudioEncoder and MusicIndex in memory."""
    _instance: Optional["SoundRecognizerService"] = None

    def __init__(self, index_path: Optional[str] = None, checkpoint_path: Optional[str] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config = AudioEncoderConfig(sample_rate=16000, backbone_type="convnet", pool_frequency=False)
        self.model = AudioEncoder(self.config)

        # Default paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.checkpoint_path = checkpoint_path or os.path.join(base_dir, "checkpoints", "audio_encoder_convnet_best.pt")
        
        if index_path is None:
            mp3_path = os.path.join(base_dir, "index_mp3.npz")
            eval_path = os.path.join(base_dir, "index_eval.npz")
            self.index_path = mp3_path if os.path.exists(mp3_path) else eval_path
        else:
            self.index_path = index_path

        # Load weights if checkpoint exists
        if os.path.exists(self.checkpoint_path):
            try:
                import sys, types
                from . import audio_encoder as _ae
                if "musiek" not in sys.modules:
                    sys.modules["musiek"] = types.ModuleType("musiek")
                if "musiek.musics" not in sys.modules:
                    try:
                        import musics
                        sys.modules["musiek.musics"] = musics
                    except ImportError:
                        pass
                sys.modules["musiek.musics.audio_encoder"] = _ae

                try:
                    ckpt = torch.load(self.checkpoint_path, map_location=self.device, weights_only=False)
                except TypeError:
                    ckpt = torch.load(self.checkpoint_path, map_location=self.device)
                self.model.load_state_dict(ckpt["model_state_dict"])
                print(f"[SoundRecognizer] Loaded trained checkpoint from {self.checkpoint_path}")
            except Exception as e:
                print(f"[SoundRecognizer] Warning: Failed to load checkpoint: {e}")

        self.model.to(self.device)
        self.model.eval()

        # Load vector index if exists
        self.index: Optional[MusicIndex] = None
        self.reload_index()

    @classmethod
    def get_instance(cls) -> "SoundRecognizerService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reload_index(self):
        """Loads or reloads the vector index from disk."""
        if os.path.exists(self.index_path):
            try:
                self.index = MusicIndex.load(self.index_path)
                print(f"[SoundRecognizer] Loaded index ({len(self.index)} slices) from {self.index_path}")
            except Exception as e:
                print(f"[SoundRecognizer] Failed loading index {self.index_path}: {e}")
                self.index = None
        else:
            self.index = None

    def recognize(
        self,
        audio_file_path: str,
        min_votes: int = 4,
        margin_threshold: float = 1.5
    ) -> MatchResult:
        """
        Recognizes an audio file using dense neural embeddings and temporal offset voting.
        
        Args:
            audio_file_path: Path to recorded query (WAV, MP3, WebM).
            min_votes: Calibrated vote threshold.
            margin_threshold: Top candidate margin ratio over runner-up.
            
        Returns:
            MatchResult dataclass.
        """
        if self.index is None or len(self.index) == 0:
            return MatchResult(
                matched=False, song_name=None, song_id=None,
                confidence=0.0, offset_seconds=0.0,
                top_votes=0, runner_up_votes=0, margin=0.0,
                details={"reason": "Index database is empty or not yet built. Run indexer/eval first."}
            )

        waveform, sr = load_audio(audio_file_path, target_sr=self.config.sample_rate)
        waveform = waveform.to(self.device)

        with torch.no_grad():
            q_embs, q_times = self.model.encode_stream(
                waveform,
                sample_rate=sr,
                hop_seconds=0.5
            )

            result = self.index.match(
                query_embeddings=q_embs,
                query_timestamps=q_times,
                top_k=30,
                time_tolerance=0.25,
                min_votes=min_votes,
                margin_threshold=margin_threshold
            )

        return result


def _clean_song_name(raw_name: str) -> str:
    """
    Converts raw filename (without extension) into a human-readable title.
    E.g. 'y2mate.com_-_Imagine_Dragons__Radioactive_Lyric_Video' -> 'Imagine Dragons  Radioactive Lyric Video'
    """
    import re
    name = os.path.splitext(raw_name)[0]
    # Strip y2mate.com_-_ prefix
    name = re.sub(r'^y\d+mate[\.\w]*[-_]+', '', name)
    # Replace double underscores with a separator, single underscores with space
    name = name.replace('__', '  ').replace('_', ' ').strip()
    return name


def recognize_audio_dl(audio_file_path: str) -> str:
    """
    Drop-in replacement for legacy recognize_audio().
    Returns matched song name or 'Unknown'.
    """
    service = SoundRecognizerService.get_instance()
    result = service.recognize(audio_file_path)

    print(f"[SoundRecognizer] Result: matched={result.matched}, "
          f"song={result.song_name!r}, votes={result.top_votes}/{result.runner_up_votes}, "
          f"margin={result.margin}, confidence={result.confidence}, "
          f"details={result.details}")

    if result.matched and result.song_name:
        # Try to resolve to human-readable title from Django Post/Music model
        try:
            from posts.models import Post
            post = Post.objects.filter(upload_file__icontains=result.song_name).first()
            if post and post.name:
                return post.name
        except Exception:
            pass

        # Try Music model
        try:
            from musics.models import Music
            music = Music.objects.filter(file__icontains=result.song_name).first()
            if music and music.name:
                return music.name
        except Exception:
            pass

        # Clean filename fallback
        return _clean_song_name(result.song_name)

    return "Unknown"
