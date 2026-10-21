"""
Dense Vector Index and Temporal Offset Voting Matcher for Sound Recognition v2.

Implements Phase 2:
- Flat inner-product vector indexing (exact cosine similarity on L2-normalized embeddings).
- Temporal offset voting: Delta = t_index - t_query.
- Calibrated dual-criterion acceptance (minimum votes + margin over runner-up).
- Disk persistence (.npz format) and memory-mapped fast loading.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Union
import os
import numpy as np
import torch
import torch.nn.functional as F


@dataclass
class MatchResult:
    matched: bool
    song_name: Optional[str]
    song_id: Optional[int]
    confidence: float
    offset_seconds: float
    top_votes: int
    runner_up_votes: int
    margin: float
    details: Dict[str, Any]


class MusicIndex:
    """
    In-memory vector database and temporal offset voting engine.
    
    Indexes audio tracks cut into 1.0s windows with 0.5s hop.
    Each window is represented by a 128-D L2-normalized vector.
    """
    def __init__(self):
        self.embeddings: Optional[np.ndarray] = None  # shape: (N, 128), float32
        self.song_ids: List[int] = []
        self.song_names: List[str] = []
        self.timestamps: List[float] = []
        self._song_catalog: Dict[int, str] = {}

    def __len__(self) -> int:
        return len(self.song_ids)

    def add_song(
        self,
        song_id: int,
        song_name: str,
        embeddings: Union[torch.Tensor, np.ndarray],
        timestamps: Union[torch.Tensor, np.ndarray]
    ):
        """
        Adds encoded embeddings of a single song into the index.
        
        Args:
            song_id: Unique integer identifier.
            song_name: Human-readable track title.
            embeddings: (NumSegments, 128) array/tensor of normalized vectors.
            timestamps: (NumSegments,) array/tensor of segment start offsets in seconds.
        """
        if isinstance(embeddings, torch.Tensor):
            embeddings = embeddings.detach().cpu().numpy()
        if isinstance(timestamps, torch.Tensor):
            timestamps = timestamps.detach().cpu().numpy()

        embeddings = embeddings.astype(np.float32)
        timestamps = timestamps.astype(np.float32)

        # Ensure L2-normalized
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

        n_segs = len(timestamps)
        new_ids = [song_id] * n_segs
        new_names = [song_name] * n_segs

        if self.embeddings is None:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])

        self.song_ids.extend(new_ids)
        self.song_names.extend(new_names)
        self.timestamps.extend(timestamps.tolist())
        self._song_catalog[song_id] = song_name

    def save(self, filepath: str):
        """Save index to compressed .npz archive."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        np.savez_compressed(
            filepath,
            embeddings=self.embeddings if self.embeddings is not None else np.empty((0, 128), dtype=np.float32),
            song_ids=np.array(self.song_ids, dtype=np.int32),
            song_names=np.array(self.song_names, dtype=object),
            timestamps=np.array(self.timestamps, dtype=np.float32)
        )

    @classmethod
    def load(cls, filepath: str) -> "MusicIndex":
        """Load index from .npz archive."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Index file not found: {filepath}")

        data = np.load(filepath, allow_pickle=True)
        index = cls()
        index.embeddings = data["embeddings"].astype(np.float32)
        index.song_ids = data["song_ids"].tolist()
        index.song_names = data["song_names"].tolist()
        index.timestamps = data["timestamps"].tolist()

        for sid, sname in zip(index.song_ids, index.song_names):
            index._song_catalog[sid] = sname

        return index

    def match(
        self,
        query_embeddings: Union[torch.Tensor, np.ndarray],
        query_timestamps: Union[torch.Tensor, np.ndarray],
        top_k: int = 30,
        time_tolerance: float = 0.25,
        min_votes: int = 4,
        margin_threshold: float = 1.5,
        sim_threshold: float = 0.40
    ) -> MatchResult:
        """
        Executes Top-K candidate search + Temporal Offset Voting.
        
        Args:
            query_embeddings: (M, 128) array/tensor of query segment vectors.
            query_timestamps: (M,) array/tensor of query segment offsets.
            top_k: Number of nearest neighbors to retrieve per query segment.
            time_tolerance: Bin width (seconds) for grouping delta = t_index - t_query.
            min_votes: Minimum votes required for acceptance.
            margin_threshold: Required ratio between top candidate votes and runner-up votes.
            sim_threshold: Minimum cosine similarity required to count as a candidate.
            
        Returns:
            MatchResult dataclass with decision, confidence, and metadata.
        """
        if self.embeddings is None or len(self.song_ids) == 0:
            return MatchResult(
                matched=False, song_name=None, song_id=None,
                confidence=0.0, offset_seconds=0.0,
                top_votes=0, runner_up_votes=0, margin=0.0,
                details={"reason": "Empty database index"}
            )

        if isinstance(query_embeddings, torch.Tensor):
            query_embeddings = query_embeddings.detach().cpu().numpy()
        if isinstance(query_timestamps, torch.Tensor):
            query_timestamps = query_timestamps.detach().cpu().numpy()

        # Query vectors L2-normalization
        q_norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
        q_norms[q_norms == 0] = 1.0
        q_normed = query_embeddings / q_norms

        # Matrix multiplication: Cosine Similarity matrix (M_query, N_database)
        sim_matrix = np.dot(q_normed, self.embeddings.T)

        m_queries = len(query_timestamps)
        effective_k = min(top_k, sim_matrix.shape[1])

        # Voting records: map (song_id, discretized_delta) -> vote_count
        # Also accumulate sum of similarities for tie-breaking
        delta_votes: Dict[Tuple[int, int], int] = {}
        delta_sims: Dict[Tuple[int, int], float] = {}
        song_total_votes: Dict[int, int] = {}

        for j in range(m_queries):
            q_time = query_timestamps[j]
            row_sims = sim_matrix[j]
            
            # Find top-k indices for query segment j
            top_indices = np.argpartition(-row_sims, effective_k - 1)[:effective_k]
            
            for idx in top_indices:
                sim = float(row_sims[idx])
                if sim < sim_threshold:
                    continue

                sid = self.song_ids[idx]
                idx_time = self.timestamps[idx]
                delta = idx_time - q_time

                # Quantize delta into discrete bins
                bin_idx = int(round(delta / time_tolerance))
                key = (sid, bin_idx)

                delta_votes[key] = delta_votes.get(key, 0) + 1
                delta_sims[key] = delta_sims.get(key, 0.0) + sim
                song_total_votes[sid] = song_total_votes.get(sid, 0) + 1

        if not delta_votes:
            return MatchResult(
                matched=False, song_name=None, song_id=None,
                confidence=0.0, offset_seconds=0.0,
                top_votes=0, runner_up_votes=0, margin=0.0,
                details={"reason": "No candidates exceeded similarity threshold"}
            )

        # --- Song-level aggregate voting (primary criterion) ---
        # song_total_votes accumulates ALL delta bins per song, solving split-vote
        # for songs with multiple similar versions in the index.
        sorted_songs = sorted(song_total_votes.items(), key=lambda kv: kv[1], reverse=True)
        best_sid_song, best_song_total = sorted_songs[0]

        # Runner-up: best different song
        runner_up_song_total = 0
        for sid, votes in sorted_songs:
            if sid != best_sid_song:
                runner_up_song_total = votes
                break

        song_margin = float(best_song_total) / float(runner_up_song_total + 1)

        # --- Delta-bucket voting (for offset estimation) ---
        # Among clusters from the winning song, find the best-voted delta bucket.
        best_delta = 0.0
        best_delta_votes = 0
        for (sid, bin_idx), votes in delta_votes.items():
            if sid == best_sid_song and votes > best_delta_votes:
                best_delta_votes = votes
                best_delta = bin_idx * time_tolerance

        # Runner-up delta bucket votes from a DIFFERENT song
        runner_up_delta_votes = 0
        sorted_delta = sorted(delta_votes.items(), key=lambda item: (item[1], delta_sims[item[0]]), reverse=True)
        for (sid, _), votes in sorted_delta:
            if sid != best_sid_song:
                runner_up_delta_votes = votes
                break

        best_song_name = self._song_catalog.get(best_sid_song, "Unknown")

        # Acceptance Criteria (song-level):
        # 1. Absolute song votes >= min_votes
        # 2. Song margin over runner-up >= margin_threshold
        is_accepted = (best_song_total >= min_votes) and (song_margin >= margin_threshold)

        # Confidence heuristic: bounded between 0.0 and 1.0
        confidence = min(1.0, (best_song_total / max(1, m_queries)) * (1.0 - 1.0 / (song_margin + 1.0)))

        return MatchResult(
            matched=is_accepted,
            song_name=best_song_name if is_accepted else None,
            song_id=best_sid_song if is_accepted else None,
            confidence=round(confidence, 4),
            offset_seconds=round(best_delta, 2),
            top_votes=best_song_total,
            runner_up_votes=runner_up_song_total,
            margin=round(song_margin, 2),
            details={
                "m_queries": m_queries,
                "best_song_name": best_song_name,
                "best_song_id": best_sid_song,
                "best_delta": best_delta,
                "best_delta_votes": best_delta_votes,
            }
        )
