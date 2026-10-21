"""
Unit Tests for Sound Recognition v2 Complete Pipeline.

Tests:
- AcousticAugmentationPipeline
- Dataset creation and track-level splitting
- Vector indexing, serialization, and temporal offset voting matching
- End-to-end forward/backward step with NT-Xent loss
"""

import unittest
import os
import shutil
import tempfile
import torch
import numpy as np

from .audio_encoder import AudioEncoder, AudioEncoderConfig, NTXentLoss
from .augment import (
    RandomGain,
    AdditiveNoise,
    SyntheticReverb,
    PhoneMicrophoneEQ,
    AcousticAugmentationPipeline
)
from .dataset import split_dataset, AudioContrastiveDataset
from .matcher import MusicIndex, MatchResult


class TestSoundRecognitionV2Pipeline(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        np.random.seed(42)
        self.temp_dir = tempfile.mkdtemp()
        self.config = AudioEncoderConfig(sample_rate=16000, backbone_type="convnet")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_augmentations_shape_and_values(self):
        # 1.0 second of audio at 16 kHz
        x = torch.sin(torch.linspace(0, 100 * 3.14159, 16000))

        gain = RandomGain()
        x_gain = gain(x)
        self.assertEqual(x_gain.shape, x.shape)

        noise = AdditiveNoise(min_snr_db=5.0, max_snr_db=10.0, p=1.0)
        x_noise = noise(x)
        self.assertEqual(x_noise.shape, x.shape)
        # Power should have increased due to noise
        self.assertGreater(torch.mean(x_noise ** 2).item(), 0.0)

        reverb = SyntheticReverb(sample_rate=16000, max_rt60=0.2, p=1.0)
        x_reverb = reverb(x)
        self.assertEqual(x_reverb.shape, x.shape)

        eq = PhoneMicrophoneEQ(p=1.0)
        x_eq = eq(x)
        self.assertEqual(x_eq.shape, x.shape)

        pipeline = AcousticAugmentationPipeline(sample_rate=16000)
        x_aug = pipeline(x)
        self.assertEqual(x_aug.shape, x.shape)
        self.assertFalse(torch.equal(x, x_aug))

    def test_split_dataset_no_leakage(self):
        dummy_files = [f"song_{i:03d}.wav" for i in range(100)]
        splits = split_dataset(dummy_files, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=123)

        train_set = set(splits["train"])
        val_set = set(splits["val"])
        test_set = set(splits["test"])

        self.assertEqual(len(train_set), 70)
        self.assertEqual(len(val_set), 15)
        self.assertEqual(len(test_set), 15)

        # Disjoint sets (Zero track leakage)
        self.assertEqual(len(train_set.intersection(val_set)), 0)
        self.assertEqual(len(train_set.intersection(test_set)), 0)
        self.assertEqual(len(val_set.intersection(test_set)), 0)

    def test_music_index_voting_and_io(self):
        index = MusicIndex()
        
        # Song 0: 10 segments
        embs_0 = torch.randn(10, 128)
        embs_0 = embs_0 / torch.norm(embs_0, dim=-1, keepdim=True)
        times_0 = torch.arange(10) * 0.5
        index.add_song(song_id=0, song_name="Track_Alpha.mp3", embeddings=embs_0, timestamps=times_0)

        # Song 1: 10 segments
        embs_1 = torch.randn(10, 128)
        embs_1 = embs_1 / torch.norm(embs_1, dim=-1, keepdim=True)
        times_1 = torch.arange(10) * 0.5
        index.add_song(song_id=1, song_name="Track_Beta.mp3", embeddings=embs_1, timestamps=times_1)

        self.assertEqual(len(index), 20)

        # Query extracted from Song 0 starting at index 2 (offset 1.0s), 4 segments long
        q_embs = embs_0[2:6].clone()
        q_times = torch.arange(4) * 0.5  # [0.0, 0.5, 1.0, 1.5]

        match_res = index.match(q_embs, q_times, top_k=5, min_votes=3, margin_threshold=1.5)
        self.assertTrue(match_res.matched)
        self.assertEqual(match_res.song_name, "Track_Alpha.mp3")
        self.assertEqual(match_res.song_id, 0)
        # Expected offset Delta = t_index (1.0) - t_query (0.0) = 1.0s
        self.assertAlmostEqual(match_res.offset_seconds, 1.0, delta=0.25)

        # Test index serialization (.npz)
        save_path = os.path.join(self.temp_dir, "test_index.npz")
        index.save(save_path)
        self.assertTrue(os.path.exists(save_path))

        loaded_index = MusicIndex.load(save_path)
        self.assertEqual(len(loaded_index), 20)
        loaded_res = loaded_index.match(q_embs, q_times, top_k=5, min_votes=3, margin_threshold=1.5)
        self.assertTrue(loaded_res.matched)
        self.assertEqual(loaded_res.song_name, "Track_Alpha.mp3")

    def test_nt_xent_training_step(self):
        model = AudioEncoder(self.config)
        criterion = NTXentLoss(temperature=0.07)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

        # Dummy batch of 4 segments: clean and noisy
        x = torch.randn(4, 16000)
        x_prime = x + torch.randn_like(x) * 0.05

        optimizer.zero_grad()
        z_i = model(x)
        z_j = model(x_prime)
        loss = criterion(z_i, z_j)

        self.assertGreater(loss.item(), 0.0)
        loss.backward()
        optimizer.step()


if __name__ == "__main__":
    unittest.main()
