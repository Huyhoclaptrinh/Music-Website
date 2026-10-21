"""
Audio Encoder Architecture for Sound Recognition v2.

This module implements the neural audio embedding models specified in DL_SOUND_RECOGNITION_PLAN.md:
- Log-Mel Spectrogram Front-End (16 kHz, n_fft=1024, hop=320, 64 mels).
- NAFP-Style ConvNet Backbone with Time-Only Pooling (preserving frequency structure).
- Conformer Backbone Alternative.
- L2-Normalized 128-D Embedding Projection.
- Stream / Sliding Window Encoding for both offline indexing and online query evaluation.
- NT-Xent Contrastive Metric Learning Loss for Phase 3 training.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Union
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio.transforms as T
from torchaudio.models import Conformer


def load_audio(file_path: str, target_sr: int = 16000) -> Tuple[torch.Tensor, int]:
    """
    Robust audio file loader that downmixes to mono and resamples to target_sr.
    Supports MP3, WAV, FLAC, OGG, AAC, WebM, and MP4 containers via soundfile, torchaudio, and pydub.
    
    Args:
        file_path: Path to audio file.
        target_sr: Desired output sampling rate (default: 16000).
        
    Returns:
        waveform: 1D torch.FloatTensor of shape (Samples,)
        sr: Output sampling rate (target_sr)
    """
    try:
        import soundfile as sf
        data, sr = sf.read(file_path, always_2d=True)
        mono_data = data.mean(axis=1)
        waveform = torch.from_numpy(mono_data).float()
    except Exception:
        try:
            import torchaudio
            waveform, sr = torchaudio.load(file_path)
            if waveform.ndim > 1:
                waveform = waveform.mean(dim=0)
        except Exception:
            try:
                from pydub import AudioSegment
                import numpy as np
                seg = AudioSegment.from_file(file_path)
                seg = seg.set_frame_rate(target_sr).set_channels(1)
                samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
                max_val = float(1 << (seg.sample_width * 8 - 1))
                if max_val > 0:
                    samples = samples / max_val
                return torch.from_numpy(samples).float(), target_sr
            except Exception as e:
                raise RuntimeError(f"Could not load audio file '{file_path}': {e}")
    
    if sr != target_sr:
        resampler = T.Resample(orig_freq=sr, new_freq=target_sr)
        waveform = resampler(waveform)
        
    return waveform, target_sr


@dataclass
class AudioEncoderConfig:
    """Hyperparameters and architectural configurations for AudioEncoder."""
    sample_rate: int = 16000          # Audio sampling rate (16 kHz baseline, 22.05 kHz ablation)
    n_fft: int = 1024                 # FFT window length
    hop_length: int = 320             # STFT hop length (20 ms at 16 kHz)
    n_mels: int = 64                  # Mel filterbank bins (64 baseline, 128 ablation)
    segment_seconds: float = 1.0      # Segment window length in seconds
    embedding_dim: int = 128          # Target L2-normalized embedding dimensionality
    backbone_type: str = "convnet"    # "convnet" (NAFP-style) or "conformer"
    pool_frequency: bool = False      # False = pool over time only (recommended); True = global avg pool (ablation)
    conformer_heads: int = 4          # Conformer attention heads
    conformer_layers: int = 4         # Conformer depth
    conformer_dim: int = 144          # Conformer model dimension


class LogMelSpectrogramFrontEnd(nn.Module):
    """
    Computes Log-Mel Spectrograms from raw audio waveforms.
    
    Front-end specification:
    - Sample rate: 16 kHz (Nyquist: 8 kHz)
    - n_fft: 1024 (frequency resolution fs / n_fft = 15.625 Hz)
    - hop_length: 320 (20 ms temporal stride)
    - n_mels: 64 (perceptual Mel scale)
    - Output: Log-compressed power spectrogram in dB.
    """
    def __init__(self, config: AudioEncoderConfig):
        super().__init__()
        self.config = config
        self.mel_transform = T.MelSpectrogram(
            sample_rate=config.sample_rate,
            n_fft=config.n_fft,
            win_length=config.n_fft,
            hop_length=config.hop_length,
            n_mels=config.n_mels,
            power=2.0,
            center=True,
            pad_mode="reflect"
        )
        self.amplitude_to_db = T.AmplitudeToDB(stype="power", top_db=80.0)

    def forward(self, waveforms: torch.Tensor) -> torch.Tensor:
        """
        Args:
            waveforms: Audio tensor of shape (Batch, Samples) or (Samples,)
        Returns:
            Log-Mel spectrogram of shape (Batch, 1, n_mels, TimeFrames)
        """
        if waveforms.ndim == 1:
            waveforms = waveforms.unsqueeze(0)
        
        # mel_transform: (Batch, n_mels, Time)
        mel_spec = self.mel_transform(waveforms)
        log_mel = self.amplitude_to_db(mel_spec)
        
        # Add channel dimension: (Batch, 1, n_mels, Time)
        return log_mel.unsqueeze(1)


class ResidualConvBlock(nn.Module):
    """2D Residual Convolutional Block with Batch Normalization and GELU activation."""
    def __init__(self, in_channels: int, out_channels: int, stride: Tuple[int, int] = (1, 1)):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.GELU(),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=(1, 1), padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
        )
        if stride != (1, 1) or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )
        else:
            self.shortcut = nn.Identity()
        
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.conv(x) + self.shortcut(x))


class ConvNetBackbone(nn.Module):
    """
    NAFP-Style Deep Convolutional Stack.
    
    Crucial Architectural Feature:
    - Audio frequency is NOT spatially translation-invariant like an image.
    - Preserves frequency structure across stages.
    - Standard mode (pool_frequency=False): Applies pooling over TIME ONLY (T -> 1),
      retaining output frequency bins (F' -> 4), flattening C_out * F' = 256 * 4 = 1024 dims.
    - Ablation mode (pool_frequency=True): Pools over BOTH frequency and time (1, 1),
      flattening C_out = 256 dims to demonstrate information loss.
    """
    def __init__(self, config: AudioEncoderConfig):
        super().__init__()
        self.config = config
        
        # Stage 1: (1, 64, T) -> (32, 32, T)
        self.stage1 = ResidualConvBlock(1, 32, stride=(2, 1))
        # Stage 2: (32, 32, T) -> (64, 16, T)
        self.stage2 = ResidualConvBlock(32, 64, stride=(2, 1))
        # Stage 3: (64, 16, T) -> (128, 8, T//2)
        self.stage3 = ResidualConvBlock(64, 128, stride=(2, 2))
        # Stage 4: (128, 8, T//2) -> (256, 4, T//4)
        self.stage4 = ResidualConvBlock(128, 256, stride=(2, 2))

        # Expected remaining frequency bins after four stride-2 frequency downsamplings:
        # 64 / 2 / 2 / 2 / 2 = 4 frequency sub-bands (or 8 for 128 mels)
        self.freq_bins_out = max(1, config.n_mels // 16)
        
        if config.pool_frequency:
            # Ablation: Global average pooling over BOTH frequency and time
            self.pool = nn.AdaptiveAvgPool2d((1, 1))
            flat_dim = 256
        else:
            # Standard: Pool over TIME ONLY, preserving frequency sub-bands
            self.pool = nn.AdaptiveAvgPool2d((self.freq_bins_out, 1))
            flat_dim = 256 * self.freq_bins_out
            
        self.projection = nn.Linear(flat_dim, config.embedding_dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (Batch, 1, F=64, T=51)
        x = self.stage1(x)  # (Batch, 32, 32, T)
        x = self.stage2(x)  # (Batch, 64, 16, T)
        x = self.stage3(x)  # (Batch, 128, 8, T//2)
        x = self.stage4(x)  # (Batch, 256, 4, T//4)
        
        x = self.pool(x)    # (Batch, 256, freq_bins_out, 1) or (Batch, 256, 1, 1)
        x = torch.flatten(x, 1)
        embeddings = self.projection(x)  # (Batch, 128)
        return embeddings


class ConformerBackbone(nn.Module):
    """
    Conformer Backbone for Audio Metric Learning.
    
    Combines 2D subsampling convolution with multi-head self-attention and
    depthwise convolutions, followed by temporal pooling and linear projection.
    """
    def __init__(self, config: AudioEncoderConfig):
        super().__init__()
        self.config = config
        d_model = config.conformer_dim
        
        # 2D Conv Subsampling: (1, F=64, T) -> (d_model, F//4=16, T)
        self.subsampling = nn.Sequential(
            nn.Conv2d(1, d_model // 2, kernel_size=3, stride=(2, 1), padding=1, bias=False),
            nn.BatchNorm2d(d_model // 2),
            nn.GELU(),
            nn.Conv2d(d_model // 2, d_model, kernel_size=3, stride=(2, 1), padding=1, bias=False),
            nn.BatchNorm2d(d_model),
            nn.GELU(),
        )
        subsampled_freq = max(1, config.n_mels // 4)
        self.linear_in = nn.Linear(d_model * subsampled_freq, d_model)
        
        self.conformer = Conformer(
            input_dim=d_model,
            num_heads=config.conformer_heads,
            ffn_dim=d_model * 4,
            num_layers=config.conformer_layers,
            depthwise_conv_kernel_size=15,
            dropout=0.1
        )
        self.projection = nn.Linear(d_model, config.embedding_dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (Batch, 1, F=64, T)
        b = x.shape[0]
        feat = self.subsampling(x)  # (B, d_model, F//4, T)
        b, c, f, t = feat.shape
        
        # Reshape to (Batch, Time, Features) for Conformer sequence processing
        seq = feat.permute(0, 3, 1, 2).contiguous().view(b, t, c * f)
        seq = self.linear_in(seq)   # (Batch, Time, d_model)
        
        lengths = torch.full((b,), t, dtype=torch.long, device=x.device)
        out, _ = self.conformer(seq, lengths)  # (Batch, Time, d_model)
        
        # Pool over TIME ONLY: mean over sequence dimension
        pooled = out.mean(dim=1)    # (Batch, d_model)
        embeddings = self.projection(pooled)  # (Batch, 128)
        return embeddings


class AudioEncoder(nn.Module):
    """
    Unified Audio Encoder Model for Sound Recognition v2.
    
    Processes raw waveform audio or pre-computed spectrograms into
    compact L2-normalized 128-D embeddings on the unit hypersphere.
    """
    def __init__(self, config: Optional[AudioEncoderConfig] = None):
        super().__init__()
        self.config = config or AudioEncoderConfig()
        self.frontend = LogMelSpectrogramFrontEnd(self.config)
        
        if self.config.backbone_type == "convnet":
            self.backbone = ConvNetBackbone(self.config)
        elif self.config.backbone_type == "conformer":
            self.backbone = ConformerBackbone(self.config)
        else:
            raise ValueError(f"Unknown backbone_type: {self.config.backbone_type}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass producing L2-normalized embeddings.
        
        Args:
            x: Raw audio waveform (Batch, Samples) or spectrogram (Batch, 1, n_mels, Time)
        Returns:
            Normalized embeddings tensor of shape (Batch, 128), ||z||_2 = 1.
        """
        if x.ndim in (1, 2):
            # Input is raw audio waveform
            spec = self.frontend(x)
        elif x.ndim == 4:
            # Input is already a 4D spectrogram
            spec = x
        else:
            raise ValueError(f"Unsupported input shape: {x.shape}")
        
        raw_embeddings = self.backbone(spec)
        normalized_embeddings = F.normalize(raw_embeddings, p=2, dim=-1)
        return normalized_embeddings

    @torch.inference_mode()
    def encode_waveform(self, waveform: torch.Tensor) -> torch.Tensor:
        """Encode a single or batched 1.0s audio clip into normalized 128-D vector(s)."""
        self.eval()
        return self.forward(waveform)

    @torch.inference_mode()
    def encode_stream(
        self,
        waveform: torch.Tensor,
        sample_rate: Optional[int] = None,
        hop_seconds: float = 0.5,
        batch_size: int = 64
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Slices a full audio track or microphone recording into overlapping 1.0s segments
        and encodes them in batches.
        
        Args:
            waveform: 1D audio tensor (Samples,) or 2D tensor (1, Samples)
            sample_rate: Sampling rate of input. If different from config.sample_rate, resampled.
            hop_seconds: Hop step between adjacent segments (default: 0.5s for 50% overlap).
            batch_size: Mini-batch size for model inference.
            
        Returns:
            embeddings: Float32 tensor of shape (NumSegments, 128)
            timestamps: Float32 tensor of start offsets in seconds (NumSegments,)
        """
        self.eval()
        if waveform.ndim == 2:
            if waveform.shape[0] > 1:
                # Downmix multi-channel to mono
                waveform = waveform.mean(dim=0)
            else:
                waveform = waveform.squeeze(0)
                
        # Resample if sample rate doesn't match config
        target_sr = self.config.sample_rate
        if sample_rate is not None and sample_rate != target_sr:
            resampler = T.Resample(orig_freq=sample_rate, new_freq=target_sr).to(waveform.device)
            waveform = resampler(waveform)

        segment_samples = int(self.config.segment_seconds * target_sr)
        hop_samples = int(hop_seconds * target_sr)
        total_samples = waveform.shape[-1]
        
        # If total audio is shorter than one segment, pad with zeros
        if total_samples < segment_samples:
            padded = F.pad(waveform, (0, segment_samples - total_samples))
            segments = padded.unsqueeze(0)
            timestamps = torch.tensor([0.0], dtype=torch.float32)
        else:
            # Unfold waveform into overlapping 1.0s slices
            # shape: (NumSegments, segment_samples)
            segments = waveform.unfold(dimension=0, size=segment_samples, step=hop_samples)
            num_segments = segments.shape[0]
            timestamps = torch.arange(num_segments, dtype=torch.float32) * hop_seconds

        all_embeddings = []
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]
            emb = self.forward(batch)
            all_embeddings.append(emb)

        embeddings = torch.cat(all_embeddings, dim=0)
        return embeddings, timestamps


class NTXentLoss(nn.Module):
    """
    Normalized Temperature-scaled Cross Entropy (NT-Xent) Loss.
    
    Used for self-supervised contrastive learning (Phase 3).
    Given pairs (z_i, z'_i) of L2-normalized vectors representing an original
    audio segment and its augmented replica:
    
    L = - sum_i log( exp(z_i . z'_i / tau) / sum_{k != i} exp(z_i . z_k / tau) )
    """
    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, z_i: torch.Tensor, z_j: torch.Tensor) -> torch.Tensor:
        """
        Args:
            z_i: Tensor of shape (Batch, 128) - normalized embeddings of original segments.
            z_j: Tensor of shape (Batch, 128) - normalized embeddings of augmented replicas.
        Returns:
            Scalar NT-Xent contrastive loss.
        """
        batch_size = z_i.shape[0]
        # Concatenate both views: shape (2 * Batch, 128)
        z = torch.cat([z_i, z_j], dim=0)
        
        # Pairwise cosine similarity matrix: (2B, 2B)
        sim = torch.mm(z, z.t()) / self.temperature
        
        # Mask out self-similarities on the main diagonal
        mask = torch.eye(2 * batch_size, dtype=torch.bool, device=z.device)
        sim = sim.masked_fill(mask, -1e9)
        
        # Targets:
        # For index i in [0..B-1], positive is i + B
        # For index i in [B..2B-1], positive is i - B
        targets = torch.cat([
            torch.arange(batch_size, 2 * batch_size, device=z.device),
            torch.arange(0, batch_size, device=z.device)
        ])
        
        loss = F.cross_entropy(sim, targets)
        return loss
