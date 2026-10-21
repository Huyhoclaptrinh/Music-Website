"""
Dataset and Data Splitting Module for Sound Recognition v2.

Provides:
- Scanning audio files across GTZAN and local media directories.
- Track-level disjoint train / val / test splitting (strictly prevents data leakage).
- PyTorch AudioContrastiveDataset producing (original, augmented) positive pairs for NT-Xent loss.
"""

import os
import random
from typing import List, Tuple, Dict, Optional
import torch
from torch.utils.data import Dataset
from .audio_encoder import load_audio
from .augment import AcousticAugmentationPipeline


def find_audio_files(directory: str, extensions: Tuple[str, ...] = (".wav", ".mp3", ".flac", ".ogg")) -> List[str]:
    """Recursively search for audio files within a directory."""
    audio_files = []
    if not os.path.exists(directory):
        return audio_files

    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(extensions) and not f.startswith("."):
                audio_files.append(os.path.join(root, f))
    audio_files.sort()
    return audio_files


def split_dataset(
    file_list: List[str],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42
) -> Dict[str, List[str]]:
    """
    Splits audio tracks into disjoint train, val, and test partitions.
    
    CRITICAL RULE:
    Splits are performed strictly at the SONG / FILE level, never on random slices,
    preventing temporal or harmonic data leakage between splits.
    
    Returns:
        Dict with keys "train", "val", "test" containing lists of file paths.
    """
    total = len(file_list)
    if total == 0:
        raise ValueError("Cannot split empty file list.")

    # Deterministic shuffle
    rng = random.Random(seed)
    shuffled = list(file_list)
    rng.shuffle(shuffled)

    n_train = int(total * train_ratio)
    n_val = int(total * val_ratio)

    train_files = shuffled[:n_train]
    val_files = shuffled[n_train:n_train + n_val]
    test_files = shuffled[n_train + n_val:]

    # Fallback if list is small
    if not test_files and len(shuffled) > 2:
        test_files = [shuffled[-1]]

    return {
        "train": train_files,
        "val": val_files,
        "test": test_files,
    }


class AudioContrastiveDataset(Dataset):
    """
    PyTorch Dataset for Self-Supervised Contrastive Metric Learning.
    
    From each audio track in the dataset:
    1. Loads the audio (resampled to 16 kHz mono).
    2. Randomly slices a 1.0-second window: x.
    3. Passes x through AcousticAugmentationPipeline to produce x'.
    4. Returns (x, x') as positive pairs for NTXentLoss.
    """
    def __init__(
        self,
        audio_files: List[str],
        sample_rate: int = 16000,
        segment_seconds: float = 1.0,
        augmentation: Optional[AcousticAugmentationPipeline] = None
    ):
        super().__init__()
        self.audio_files = audio_files
        self.sample_rate = sample_rate
        self.segment_samples = int(segment_seconds * sample_rate)
        self.augmentation = augmentation or AcousticAugmentationPipeline(sample_rate=sample_rate)

    def __len__(self) -> int:
        return len(self.audio_files)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        file_path = self.audio_files[idx]
        try:
            waveform, _ = load_audio(file_path, target_sr=self.sample_rate)
        except Exception:
            # Fallback to zeros on corrupted audio file
            waveform = torch.zeros(self.segment_samples, dtype=torch.float32)

        total_samples = waveform.shape[-1]
        if total_samples < self.segment_samples:
            # Pad with zeros
            x = torch.zeros(self.segment_samples, dtype=torch.float32)
            x[:total_samples] = waveform
        else:
            # Random temporal slice
            max_start = total_samples - self.segment_samples
            start_idx = random.randint(0, max_start)
            x = waveform[start_idx : start_idx + self.segment_samples]

        # Generate augmented view
        with torch.no_grad():
            x_prime = self.augmentation(x)

        return x, x_prime
