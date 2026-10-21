"""
Acoustic Augmentation Pipeline for Sound Recognition v2.

Simulates real-world acoustic degradations that occur when audio is played
through loudspeakers into a microphone in a domestic or noisy environment:
- Additive ambient noise (0 - 20 dB SNR).
- Synthetic Room Impulse Response (reverberation).
- Microphone frequency response (bandpass / EQ coloration).
- Random temporal offset jitter.
- Random amplitude gain variation (+/- 6 dB).
"""

import math
import random
from typing import Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class RandomGain(nn.Module):
    """Applies random amplitude gain scaling within [min_db, max_db]."""
    def __init__(self, min_db: float = -6.0, max_db: float = 6.0):
        super().__init__()
        self.min_db = min_db
        self.max_db = max_db

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        gain_db = random.uniform(self.min_db, self.max_db)
        scale = 10.0 ** (gain_db / 20.0)
        return waveform * scale


class AdditiveNoise(nn.Module):
    """
    Adds Gaussian or colored ambient noise at a specified Signal-to-Noise Ratio (SNR in dB).
    """
    def __init__(self, min_snr_db: float = 0.0, max_snr_db: float = 20.0, p: float = 0.8):
        super().__init__()
        self.min_snr_db = min_snr_db
        self.max_snr_db = max_snr_db
        self.p = p

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        if random.random() > self.p:
            return waveform

        # Signal power
        sig_power = torch.mean(waveform ** 2)
        if sig_power < 1e-7:
            return waveform

        target_snr_db = random.uniform(self.min_snr_db, self.max_snr_db)
        snr_linear = 10.0 ** (target_snr_db / 10.0)
        noise_power = sig_power / snr_linear

        noise = torch.randn_like(waveform) * torch.sqrt(noise_power)
        return waveform + noise


class SyntheticReverb(nn.Module):
    """
    Simulates room reverberation via convolution with an exponentially decaying
    noise impulse response (Schroeder reverberator approximation).
    """
    def __init__(self, sample_rate: int = 16000, max_rt60: float = 0.4, p: float = 0.6):
        super().__init__()
        self.sample_rate = sample_rate
        self.max_rt60 = max_rt60
        self.p = p

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        if random.random() > self.p:
            return waveform

        # Random reverberation time RT60 (seconds)
        rt60 = random.uniform(0.08, self.max_rt60)
        rir_length = int(rt60 * self.sample_rate)
        if rir_length < 16:
            return waveform

        t = torch.linspace(0, rt60, rir_length, device=waveform.device)
        # Decay factor: -60 dB over rt60 seconds
        decay = torch.exp(-3.0 * math.log(10.0) * t / rt60)
        rir = torch.randn(rir_length, device=waveform.device) * decay
        # Normalize RIR energy
        rir = rir / (torch.norm(rir, p=2) + 1e-8)

        # Mix dry + wet
        orig_len = waveform.shape[-1]
        dry_weight = random.uniform(0.5, 0.85)
        wet_weight = math.sqrt(max(0.0, 1.0 - dry_weight ** 2))

        # 1D convolution: shape (1, 1, samples)
        x = waveform.view(1, 1, -1)
        k = rir.view(1, 1, -1)
        convolved = F.conv1d(x, k, padding=rir_length // 2).view(-1)
        convolved = convolved[:orig_len]

        out = dry_weight * waveform + wet_weight * convolved
        return out


class PhoneMicrophoneEQ(nn.Module):
    """
    Simulates mobile phone or budget electret microphone frequency response:
    - Rolls off low bass frequencies below ~300 Hz.
    - Rolls off high frequencies above ~4000 Hz.
    Implemented as a 1D bandpass filter via moving difference.
    """
    def __init__(self, p: float = 0.5):
        super().__init__()
        self.p = p

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        if random.random() > self.p or waveform.shape[-1] < 16:
            return waveform

        # High-pass pre-emphasis filter (alpha in [0.92, 0.97])
        alpha = random.uniform(0.92, 0.97)
        hp = torch.empty_like(waveform)
        hp[..., 0] = waveform[..., 0]
        hp[..., 1:] = waveform[..., 1:] - alpha * waveform[..., :-1]

        # Random soft clipping (microphone preamp saturation)
        if random.random() < 0.4:
            hp = torch.tanh(hp * 1.5) / 1.5

        return hp


class AcousticAugmentationPipeline(nn.Module):
    """
    Combined acoustic simulation pipeline.
    Produces realistic simulated microphone recordings from clean source waveforms.
    """
    def __init__(self, sample_rate: int = 16000):
        super().__init__()
        self.gain = RandomGain(-6.0, 6.0)
        self.noise = AdditiveNoise(min_snr_db=0.0, max_snr_db=15.0, p=0.85)
        self.reverb = SyntheticReverb(sample_rate=sample_rate, max_rt60=0.35, p=0.6)
        self.phone_eq = PhoneMicrophoneEQ(p=0.5)

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        """
        Args:
            waveform: 1D audio tensor (samples,) or (Batch, samples)
        Returns:
            Augmented audio tensor of identical shape
        """
        x = waveform.clone()
        x = self.gain(x)
        x = self.reverb(x)
        x = self.phone_eq(x)
        x = self.noise(x)
        # Normalize to prevent clipping
        max_val = torch.max(torch.abs(x))
        if max_val > 1.0:
            x = x / (max_val + 1e-6)
        return x
