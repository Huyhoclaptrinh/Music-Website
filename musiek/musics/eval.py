"""
Evaluation and Benchmark Harness for Sound Recognition v2.

Implements Phase 0 and Phase 1:
- Indexes in-library database tracks using AudioEncoder + MusicIndex.
- Generates synthetic microphone query clips at varying durations (3s, 5s, 10s) and SNRs.
- Generates out-of-library query clips to evaluate False-Accept Rate (FAR).
- Measures Top-1 Hit Rate, Offset Error, FAR, and Latency.

Usage:
    python -m musiek.musics.eval --data_dir gtzan_data/Data/genres_original --num_tracks 50 --query_seconds 5.0
"""

import argparse
import os
import random
import time
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import torch
from .audio_encoder import AudioEncoder, AudioEncoderConfig, load_audio
from .dataset import find_audio_files, split_dataset
from .augment import AcousticAugmentationPipeline
from .matcher import MusicIndex


def build_database_index(
    model: AudioEncoder,
    audio_files: List[str],
    device: torch.device
) -> Tuple[MusicIndex, List[str]]:
    """Indexes tracks into a MusicIndex instance, returning the index and valid files."""
    index = MusicIndex()
    model.eval()
    valid_files = []
    print(f"[*] Indexing {len(audio_files)} database tracks...")

    for song_id, file_path in enumerate(audio_files):
        song_name = os.path.basename(file_path)
        try:
            waveform, sr = load_audio(file_path, target_sr=16000)
            waveform = waveform.to(device)
            with torch.no_grad():
                embeddings, timestamps = model.encode_stream(waveform, sample_rate=sr, hop_seconds=0.5)
            index.add_song(song_id, song_name, embeddings, timestamps)
            valid_files.append(file_path)
        except Exception as e:
            print(f"[!] Warning: Failed to index {song_name}: {e}")

    print(f"[✓] Database indexing complete. Total indexed slices: {len(index)} ({len(valid_files)} valid songs).")
    return index, valid_files


def generate_query_clip(
    file_path: str,
    query_seconds: float,
    augmentation: AcousticAugmentationPipeline
) -> Tuple[Optional[torch.Tensor], float]:
    """
    Extracts a random sub-clip of `query_seconds` from an audio file,
    returns the augmented clip and its true start offset in seconds.
    """
    try:
        waveform, sr = load_audio(file_path, target_sr=16000)
    except Exception as e:
        print(f"[!] Warning: Failed to load query {os.path.basename(file_path)}: {e}")
        return None, 0.0

    query_samples = int(query_seconds * 16000)
    total_samples = waveform.shape[-1]

    if total_samples <= query_samples:
        clip = torch.zeros(query_samples, dtype=torch.float32)
        clip[:total_samples] = waveform
        true_offset = 0.0
    else:
        max_start = total_samples - query_samples
        start_idx = random.randint(0, max_start)
        clip = waveform[start_idx : start_idx + query_samples]
        true_offset = float(start_idx) / 16000.0

    # Apply realistic acoustic degradation
    with torch.no_grad():
        noisy_clip = augmentation(clip)

    return noisy_clip, true_offset


def run_benchmark(
    model: AudioEncoder,
    index: MusicIndex,
    in_library_files: List[str],
    out_of_library_files: List[str],
    query_seconds: float = 5.0,
    num_queries: int = 40,
    device: torch.device = torch.device("cpu")
) -> Dict[str, Any]:
    """Runs end-to-end evaluation benchmark."""
    model.eval()
    aug = AcousticAugmentationPipeline(sample_rate=16000)

    in_correct = 0
    in_total = min(num_queries, len(in_library_files))
    offset_errors = []
    latencies = []

    print(f"\n[*] Evaluating In-Library Queries (Length: {query_seconds}s, Total: {in_total})...")

    # Sample random tracks for in-library queries
    sampled_in_files = random.sample(in_library_files, in_total)
    for i, file_path in enumerate(sampled_in_files):
        true_song_name = os.path.basename(file_path)
        clip, true_offset = generate_query_clip(file_path, query_seconds, aug)
        if clip is None:
            continue
        clip = clip.to(device)

        t0 = time.perf_counter()
        with torch.no_grad():
            q_embs, q_times = model.encode_stream(clip, sample_rate=16000, hop_seconds=0.5)
            match_res = index.match(
                q_embs, q_times,
                top_k=30,
                min_votes=max(2, int(query_seconds * 0.8)),
                margin_threshold=1.5
            )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

        if match_res.matched and match_res.song_name == true_song_name:
            in_correct += 1
            offset_err = abs(match_res.offset_seconds - true_offset)
            offset_errors.append(offset_err)

    top1_hit_rate = (in_correct / max(1, in_total)) * 100.0
    mean_offset_err = np.mean(offset_errors) if offset_errors else float("nan")

    # Out-of-library evaluation (False-Accept Rate)
    out_total = min(num_queries, len(out_of_library_files))
    out_false_accepts = 0

    if out_total > 0:
        print(f"[*] Evaluating Out-of-Library Queries (Total: {out_total})...")
        sampled_out_files = random.sample(out_of_library_files, out_total)
        for file_path in sampled_out_files:
            clip, _ = generate_query_clip(file_path, query_seconds, aug)
            if clip is None:
                continue
            clip = clip.to(device)
            with torch.no_grad():
                q_embs, q_times = model.encode_stream(clip, sample_rate=16000, hop_seconds=0.5)
                match_res = index.match(
                    q_embs, q_times,
                    top_k=30,
                    min_votes=max(2, int(query_seconds * 0.8)),
                    margin_threshold=1.5
                )
            if match_res.matched:
                out_false_accepts += 1

    far = (out_false_accepts / max(1, out_total)) * 100.0 if out_total > 0 else 0.0

    return {
        "query_seconds": query_seconds,
        "in_library_queries": in_total,
        "top1_hit_rate_pct": top1_hit_rate,
        "mean_offset_err_sec": mean_offset_err,
        "out_of_library_queries": out_total,
        "false_accept_rate_pct": far,
        "latency_mean_ms": np.mean(latencies),
        "latency_p95_ms": np.percentile(latencies, 95) if latencies else 0.0,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Sound Recognition v2 system.")
    parser.add_argument("--data_dir", type=str, default="gtzan_data/Data/genres_original",
                        help="Path to audio tracks directory.")
    parser.add_argument("--num_tracks", type=int, default=50,
                        help="Max number of tracks to use for evaluation.")
    parser.add_argument("--query_seconds", type=float, default=5.0,
                        help="Length of simulated query snippet (seconds).")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Path to trained model checkpoint .pt (optional).")
    parser.add_argument("--save_index", type=str, default="musiek/musics/index_eval.npz",
                        help="Path to save or cache the built index.")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Running evaluation on device: {device}")

    # Load model
    config = AudioEncoderConfig(sample_rate=16000, backbone_type="convnet", pool_frequency=False)
    model = AudioEncoder(config)

    if args.checkpoint and os.path.exists(args.checkpoint):
        print(f"[*] Loading checkpoint from: {args.checkpoint}")
        try:
            ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
        except TypeError:
            ckpt = torch.load(args.checkpoint, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        print("[*] Using randomly initialized AudioEncoder (Baseline mode).")

    model = model.to(device)

    # Audio files
    all_files = find_audio_files(args.data_dir)
    if not all_files:
        print(f"[!] No audio files found in {args.data_dir}.")
        return

    # Subsample if requested
    if len(all_files) > args.num_tracks:
        all_files = all_files[:args.num_tracks]

    # Split into indexed songs (70%) and out-of-library songs (30%)
    split_idx = int(len(all_files) * 0.70)
    in_library_files = all_files[:split_idx]
    out_of_library_files = all_files[split_idx:]

    print(f"[*] In-Library Database Songs: {len(in_library_files)}")
    print(f"[*] Out-of-Library (Unseen) Songs: {len(out_of_library_files)}")

    # Index in-library tracks
    index, valid_in_files = build_database_index(model, in_library_files, device)
    if args.save_index:
        index.save(args.save_index)
        print(f"[✓] Saved index to {args.save_index}")

    # Run Benchmark
    results = run_benchmark(
        model=model,
        index=index,
        in_library_files=valid_in_files if valid_in_files else in_library_files,
        out_of_library_files=out_of_library_files,
        query_seconds=args.query_seconds,
        num_queries=min(len(valid_in_files), 30) if valid_in_files else 0,
        device=device
    )

    # Display Report
    print("\n" + "=" * 60)
    print("       SOUND RECOGNITION V2: BENCHMARK REPORT")
    print("=" * 60)
    print(f" Query Duration:          {results['query_seconds']:.1f} seconds")
    print(f" In-Library Queries:      {results['in_library_queries']}")
    print(f" Top-1 Hit Rate:          {results['top1_hit_rate_pct']:.2f}%")
    print(f" Offset Error (MAE):      {results['mean_offset_err_sec']:.3f} seconds")
    print(f" Out-of-Library Queries:  {results['out_of_library_queries']}")
    print(f" False-Accept Rate (FAR): {results['false_accept_rate_pct']:.2f}% (Target: < 1.0%)")
    print(f" Mean Query Latency:      {results['latency_mean_ms']:.2f} ms")
    print(f" P95 Query Latency:       {results['latency_p95_ms']:.2f} ms")
    print("=" * 60)


if __name__ == "__main__":
    main()
