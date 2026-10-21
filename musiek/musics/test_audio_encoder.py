"""
Unit Tests for Sound Recognition v2 Audio Encoder.
"""

import unittest
import torch
import torchaudio
import os
from .audio_encoder import (
    AudioEncoderConfig,
    LogMelSpectrogramFrontEnd,
    ConvNetBackbone,
    ConformerBackbone,
    AudioEncoder,
    NTXentLoss,
)


class TestAudioEncoderArchitecture(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        self.config_convnet = AudioEncoderConfig(
            sample_rate=16000,
            n_fft=1024,
            hop_length=320,
            n_mels=64,
            segment_seconds=1.0,
            embedding_dim=128,
            backbone_type="convnet",
            pool_frequency=False,
        )
        self.config_conformer = AudioEncoderConfig(
            sample_rate=16000,
            n_fft=1024,
            hop_length=320,
            n_mels=64,
            segment_seconds=1.0,
            embedding_dim=128,
            backbone_type="conformer",
            conformer_heads=4,
            conformer_layers=2,
            conformer_dim=64,
        )

    def test_log_mel_frontend(self):
        frontend = LogMelSpectrogramFrontEnd(self.config_convnet)
        # 1.0s of audio at 16 kHz = 16,000 samples
        waveform = torch.randn(2, 16000)
        spec = frontend(waveform)
        self.assertEqual(spec.ndim, 4)
        self.assertEqual(spec.shape[0], 2)
        self.assertEqual(spec.shape[1], 1)
        self.assertEqual(spec.shape[2], 64)  # 64 mel bins
        self.assertEqual(spec.shape[3], 51)  # 51 frames (center=True, hop=320)

    def test_convnet_time_only_pooling(self):
        model = AudioEncoder(self.config_convnet)
        waveform = torch.randn(4, 16000)
        embeddings = model(waveform)
        
        # Verify shape
        self.assertEqual(embeddings.shape, (4, 128))
        
        # Verify L2 normalization
        norms = torch.norm(embeddings, p=2, dim=-1)
        self.assertTrue(torch.allclose(norms, torch.ones_like(norms), atol=1e-5))

    def test_convnet_ablation_frequency_pooling(self):
        config_ablation = AudioEncoderConfig(
            sample_rate=16000,
            n_mels=64,
            embedding_dim=128,
            backbone_type="convnet",
            pool_frequency=True,  # Ablation toggle
        )
        model = AudioEncoder(config_ablation)
        waveform = torch.randn(3, 16000)
        embeddings = model(waveform)
        self.assertEqual(embeddings.shape, (3, 128))
        norms = torch.norm(embeddings, p=2, dim=-1)
        self.assertTrue(torch.allclose(norms, torch.ones_like(norms), atol=1e-5))

    def test_conformer_backbone(self):
        model = AudioEncoder(self.config_conformer)
        waveform = torch.randn(2, 16000)
        embeddings = model(waveform)
        self.assertEqual(embeddings.shape, (2, 128))
        norms = torch.norm(embeddings, p=2, dim=-1)
        self.assertTrue(torch.allclose(norms, torch.ones_like(norms), atol=1e-5))

    def test_encode_stream_sliding_windows(self):
        model = AudioEncoder(self.config_convnet)
        # 3.0 seconds audio at 16 kHz = 48,000 samples
        # With 1.0s window and 0.5s hop:
        # Window 0: [0.0s - 1.0s] (offset 0.0s)
        # Window 1: [0.5s - 1.5s] (offset 0.5s)
        # Window 2: [1.0s - 2.0s] (offset 1.0s)
        # Window 3: [1.5s - 2.5s] (offset 1.5s)
        # Window 4: [2.0s - 3.0s] (offset 2.0s)
        # Expected: 5 segments
        waveform = torch.randn(48000)
        embeddings, timestamps = model.encode_stream(waveform, hop_seconds=0.5)
        
        self.assertEqual(embeddings.shape, (5, 128))
        self.assertEqual(timestamps.shape, (5,))
        expected_timestamps = torch.tensor([0.0, 0.5, 1.0, 1.5, 2.0])
        self.assertTrue(torch.allclose(timestamps, expected_timestamps))
        
        # Verify all embeddings are unit-normalized
        norms = torch.norm(embeddings, p=2, dim=-1)
        self.assertTrue(torch.allclose(norms, torch.ones_like(norms), atol=1e-5))

    def test_load_audio_file(self):
        from .audio_encoder import load_audio
        audio_path = "musiek/media/audio/Wildfire_HSR.mp3"
        if os.path.exists(audio_path):
            waveform, sr = load_audio(audio_path, target_sr=16000)
            self.assertEqual(sr, 16000)
            self.assertEqual(waveform.ndim, 1)
            self.assertGreater(waveform.shape[0], 0)

    def test_nt_xent_loss(self):
        criterion = NTXentLoss(temperature=0.07)
        # 8 positive pairs
        z1 = torch.randn(8, 128)
        z1 = torch.nn.functional.normalize(z1, p=2, dim=-1)
        # Perfect match: z2 == z1
        loss_perfect = criterion(z1, z1)
        
        # Slightly noisy match
        z2 = torch.nn.functional.normalize(z1 + 0.1 * torch.randn(8, 128), p=2, dim=-1)
        loss_noisy = criterion(z1, z2)
        
        # Random match
        z_random = torch.nn.functional.normalize(torch.randn(8, 128), p=2, dim=-1)
        loss_random = criterion(z1, z_random)
        
        # Loss should be lowest for perfect match, then noisy, then random
        self.assertLess(loss_perfect.item(), loss_noisy.item())
        self.assertLess(loss_noisy.item(), loss_random.item())


if __name__ == "__main__":
    unittest.main()
