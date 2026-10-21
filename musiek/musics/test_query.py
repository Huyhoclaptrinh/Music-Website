"""
Single Song Recognition CLI Tester for Sound Recognition v2.

Allows testing any audio file or picking a random song from the dataset,
cutting a sub-segment (with optional acoustic noise simulation), and
letting the neural model predict the song title and timestamp offset.

Usage:
    # 1. Test a random song from GTZAN:
    python -m musiek.musics.test_query --random --duration 5.0

    # 2. Test a specific audio file:
    python -m musiek.musics.test_query --audio gtzan_data/Data/genres_original/blues/blues.00012.wav --duration 5.0
"""

import argparse
import os
import random
import time
import torch
import numpy as np

from .audio_encoder import AudioEncoder, AudioEncoderConfig, load_audio
from .matcher import MusicIndex
from .augment import AcousticAugmentationPipeline


def main():
    parser = argparse.ArgumentParser(description="Test Sound Recognition on a single audio clip.")
    parser.add_argument("--index", type=str, default="musiek/musics/index_eval.npz",
                        help="Path to the indexed .npz database.")
    parser.add_argument("--checkpoint", type=str, default="musiek/musics/checkpoints/audio_encoder_convnet_best.pt",
                        help="Path to trained model checkpoint.")
    parser.add_argument("--audio", type=str, default=None,
                        help="Path to a specific audio file to test.")
    parser.add_argument("--random", action="store_true",
                        help="Pick a random song from the indexed catalog.")
    parser.add_argument("--data_dir", type=str, default="gtzan_data/Data/genres_original",
                        help="Directory to pick random audio from if --random is used.")
    parser.add_argument("--duration", type=float, default=5.0,
                        help="Duration in seconds for the recorded query clip (e.g. 3.0, 5.0, 10.0).")
    parser.add_argument("--noisy", action="store_true", default=True,
                        help="Simulate realistic room noise, reverb, and phone mic EQ.")
    parser.add_argument("--clean", action="store_true",
                        help="Do NOT add acoustic noise; test clean audio.")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 1. Load Vector Index
    if not os.path.exists(args.index):
        print(f"[!] Error: Index file '{args.index}' does not exist.")
        print("[!] Please build the index first using eval.py or pass --index <path>.")
        return

    print(f"[*] Loading index from: {args.index}")
    index = MusicIndex.load(args.index)
    catalog = list(index._song_catalog.values())
    print(f"[✓] Index loaded successfully. Contains {len(catalog)} songs ({len(index)} total segments).")

    # 2. Select Audio File to Test
    target_file = None
    if args.audio:
        target_file = args.audio
    else:
        # Pick random song from catalog
        chosen_name = random.choice(catalog)
        # Search for this file in data_dir
        for root, _, files in os.walk(args.data_dir):
            if chosen_name in files:
                target_file = os.path.join(root, chosen_name)
                break

    if not target_file or not os.path.exists(target_file):
        print(f"[!] Could not locate file for query: {target_file}")
        return

    print(f"\n" + "=" * 60)
    print(f"[*] TARGET SONG: {os.path.basename(target_file)}")
    print("=" * 60)

    # 3. Load Audio and Cut a Random Snippet
    waveform, sr = load_audio(target_file, target_sr=16000)
    query_samples = int(args.duration * 16000)
    total_samples = waveform.shape[-1]

    if total_samples <= query_samples:
        start_sample = 0
        clip = waveform
    else:
        max_start = total_samples - query_samples
        start_sample = random.randint(0, max_start)
        clip = waveform[start_sample : start_sample + query_samples]

    true_start_sec = start_sample / 16000.0
    print(f"[*] Extracted {args.duration:.1f}s clip from offset: {true_start_sec:.2f}s - {true_start_sec + args.duration:.2f}s")

    # Apply acoustic noise simulation if not explicitly clean
    if not args.clean:
        print("[*] Applying real-world acoustic simulation (ambient noise + reverb + phone EQ)...")
        aug = AcousticAugmentationPipeline(sample_rate=16000)
        with torch.no_grad():
            query_waveform = aug(clip)
    else:
        print("[*] Testing clean clip (no noise added)...")
        query_waveform = clip

    # 4. Load Neural Encoder Model
    config = AudioEncoderConfig(sample_rate=16000, backbone_type="convnet", pool_frequency=False)
    model = AudioEncoder(config)

    if os.path.exists(args.checkpoint):
        try:
            ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
        except TypeError:
            ckpt = torch.load(args.checkpoint, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        print(f"[*] Loaded trained checkpoint from {args.checkpoint}")
    else:
        print("[*] Warning: Trained checkpoint not found, using untrained baseline.")

    model.to(device)
    model.eval()

    # 5. Model Inference & Matching
    query_waveform = query_waveform.to(device)
    t0 = time.perf_counter()
    with torch.no_grad():
        q_embs, q_times = model.encode_stream(query_waveform, sample_rate=16000, hop_seconds=0.5)
        match_result = index.match(
            query_embeddings=q_embs,
            query_timestamps=q_times,
            top_k=30,
            min_votes=max(2, int(args.duration * 0.8)),
            margin_threshold=1.5
        )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # 6. Show Prediction Results
    expected_name = os.path.basename(target_file)
    is_correct = match_result.matched and (match_result.song_name == expected_name)

    print("\n" + "=" * 60)
    print("                    MODEL PREDICTION")
    print("=" * 60)
    print(f" Expected Song:    {expected_name}")
    print(f" Predicted Song:   {match_result.song_name if match_result.matched else 'UNKNOWN SONG (Rejected)'}")
    print(f" Match Result:     {'CORRECT MATCH' if is_correct else 'MISMATCH OR UNKNOWN'}")
    print(f" Confidence Score: {match_result.confidence * 100:.1f}%")
    print(f" Top Votes:        {match_result.top_votes} votes (vs. runner-up: {match_result.runner_up_votes})")
    print(f" Voting Margin:    {match_result.margin:.2f}x (ratio over 2nd place)")
    print(f" Predicted Offset: {match_result.offset_seconds:.2f}s (True Offset: {true_start_sec:.2f}s)")
    if match_result.matched:
        offset_error = abs(match_result.offset_seconds - true_start_sec)
        print(f" Offset Error:     {offset_error:.3f} seconds")
    print(f" Inference Time:   {elapsed_ms:.2f} ms")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
