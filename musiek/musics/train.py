"""
Contrastive Metric Learning Training Script for Sound Recognition v2.

Implements Phase 3:
- Self-supervised training using NT-Xent (Normalized Temperature-scaled Cross Entropy) loss.
- Track-level train / val splitting (no track leakage).
- Dynamic acoustic simulation augmentation.
- Model checkpointing.

Usage:
    python -m musiek.musics.train --data_dir gtzan_data/Data/genres_original --epochs 10 --batch_size 32
"""

import argparse
import os
import time
import torch
from torch.utils.data import DataLoader
from .audio_encoder import AudioEncoder, AudioEncoderConfig, NTXentLoss
from .dataset import find_audio_files, split_dataset, AudioContrastiveDataset
from .augment import AcousticAugmentationPipeline


def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    count = 0

    for x, x_prime in dataloader:
        x = x.to(device)
        x_prime = x_prime.to(device)

        optimizer.zero_grad()
        z_i = model(x)
        z_j = model(x_prime)

        loss = criterion(z_i, z_j)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * x.size(0)
        count += x.size(0)

    return total_loss / max(1, count)


@torch.no_grad()
def eval_epoch(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    count = 0

    for x, x_prime in dataloader:
        x = x.to(device)
        x_prime = x_prime.to(device)

        z_i = model(x)
        z_j = model(x_prime)

        loss = criterion(z_i, z_j)
        total_loss += loss.item() * x.size(0)
        count += x.size(0)

    return total_loss / max(1, count)


def main():
    parser = argparse.ArgumentParser(description="Train AudioEncoder via Contrastive Metric Learning.")
    parser.add_argument("--data_dir", type=str, default="gtzan_data/Data/genres_original",
                        help="Path to audio tracks directory (e.g. GTZAN or media/audio).")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=32, help="Mini-batch size.")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate.")
    parser.add_argument("--temperature", type=float, default=0.07, help="NT-Xent temperature parameter.")
    parser.add_argument("--save_dir", type=str, default="musiek/musics/checkpoints",
                        help="Directory to save model checkpoints.")
    parser.add_argument("--backbone", type=str, default="convnet", choices=["convnet", "conformer"],
                        help="Backbone architecture.")
    parser.add_argument("--num_workers", type=int, default=2, help="DataLoader worker processes.")
    args = parser.parse_args()

    # Device selection
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    print(f"[*] Training on device: {device}")

    # Discover audio files
    all_files = find_audio_files(args.data_dir)
    print(f"[*] Found {len(all_files)} total audio files in '{args.data_dir}'.")
    if len(all_files) == 0:
        print("[!] No audio files found. Please check --data_dir.")
        return

    # Disjoint split
    splits = split_dataset(all_files, train_ratio=0.75, val_ratio=0.15, test_ratio=0.10)
    train_files = splits["train"]
    val_files = splits["val"]
    print(f"[*] Track-level split -> Train: {len(train_files)}, Val: {len(val_files)}, Test: {len(splits['test'])}")

    # Datasets and Loaders
    train_dataset = AudioContrastiveDataset(train_files, sample_rate=16000)
    val_dataset = AudioContrastiveDataset(val_files, sample_rate=16000)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        drop_last=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        drop_last=False
    )

    # Initialize model and loss
    config = AudioEncoderConfig(sample_rate=16000, backbone_type=args.backbone, pool_frequency=False)
    model = AudioEncoder(config).to(device)
    criterion = NTXentLoss(temperature=args.temperature).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    os.makedirs(args.save_dir, exist_ok=True)
    best_val_loss = float("inf")
    best_ckpt_path = os.path.join(args.save_dir, f"audio_encoder_{args.backbone}_best.pt")

    print(f"[*] Starting training for {args.epochs} epochs...")
    print("-" * 65)

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = eval_epoch(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.time() - t0

        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "config": config,
                "val_loss": val_loss,
            }, best_ckpt_path)

        mark = " (best -> saved)" if is_best else ""
        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] - Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Time: {elapsed:.2f}s{mark}")

    print("-" * 65)
    print(f"[✓] Training complete. Best model checkpoint saved to: {best_ckpt_path}")


if __name__ == "__main__":
    main()
