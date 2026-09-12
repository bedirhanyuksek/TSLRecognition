from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
import yaml
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

from chatsl_ml.landmark_data import LandmarkDataset
from chatsl_ml.landmark_model import LandmarkTCN
from chatsl_ml.train import select_device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    return parser.parse_args()


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: AdamW | None = None,
    gradient_clip_norm: float | None = None,
) -> tuple[float, float, float]:
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    total_correct = 0
    total_top5_correct = 0
    total_samples = 0

    for sequences, labels in loader:
        sequences = sequences.to(device).contiguous()
        labels = labels.to(device)
        with torch.set_grad_enabled(training):
            logits = model(sequences)
            loss = criterion(logits, labels)
            if training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                if gradient_clip_norm is not None:
                    nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
                optimizer.step()

        total_loss += loss.item() * labels.size(0)
        total_correct += (logits.argmax(dim=1) == labels).sum().item()
        top5 = logits.topk(k=min(5, logits.shape[1]), dim=1).indices
        total_top5_correct += top5.eq(labels[:, None]).any(dim=1).sum().item()
        total_samples += labels.size(0)

    return (
        total_loss / total_samples,
        total_correct / total_samples,
        total_top5_correct / total_samples,
    )


def main() -> None:
    args = parse_args()
    with args.config.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    random.seed(config["seed"])
    np.random.seed(config["seed"])
    torch.manual_seed(config["seed"])

    root = Path.cwd()
    data_config = config["data"]
    limit = 8 if args.smoke_test else None
    train_dataset = LandmarkDataset(
        root / data_config["train_manifest"],
        root / data_config["train_landmarks"],
        limit=limit,
        feature_mode=data_config.get(
            "train_feature_mode",
            data_config.get("feature_mode", "full"),
        ),
    )
    val_dataset = LandmarkDataset(
        root / data_config["val_manifest"],
        root / data_config["val_landmarks"],
        limit=limit,
        feature_mode=data_config.get(
            "val_feature_mode",
            data_config.get("feature_mode", "full"),
        ),
    )
    training = config["training"]
    batch_size = 2 if args.smoke_test else training["batch_size"]
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=training["num_workers"],
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        num_workers=training["num_workers"],
    )

    sample_features, _ = train_dataset[0]
    model_config = config["model"]
    model = LandmarkTCN(
        input_size=sample_features.shape[1],
        hidden_size=model_config["hidden_size"],
        num_classes=config["num_classes"],
        dropout=model_config["dropout"],
    )
    device = select_device(args.device)
    model.to(device)
    optimizer = AdamW(
        model.parameters(),
        lr=training["learning_rate"],
        weight_decay=training["weight_decay"],
    )
    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=training["lr_factor"],
        patience=training["lr_patience"],
        min_lr=training["min_learning_rate"],
    )
    criterion = nn.CrossEntropyLoss()
    epochs = 1 if args.smoke_test else training["epochs"]
    output_dir = root / training["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        json.dumps(
            {
                "device": str(device),
                "input_size": sample_features.shape[1],
                "frames": sample_features.shape[0],
                "train_samples": len(train_dataset),
                "val_samples": len(val_dataset),
                "trainable_parameters": sum(p.numel() for p in model.parameters()),
            }
        ),
        flush=True,
    )

    best_accuracy = -1.0
    stale_epochs = 0
    for epoch in range(1, epochs + 1):
        train_metrics = run_epoch(
            model,
            train_loader,
            criterion,
            device,
            optimizer,
            training["gradient_clip_norm"],
        )
        with torch.no_grad():
            val_metrics = run_epoch(model, val_loader, criterion, device)
        metrics = {
            "epoch": epoch,
            "learning_rate": optimizer.param_groups[0]["lr"],
            "train_loss": train_metrics[0],
            "train_accuracy": train_metrics[1],
            "train_top5_accuracy": train_metrics[2],
            "val_loss": val_metrics[0],
            "val_accuracy": val_metrics[1],
            "val_top5_accuracy": val_metrics[2],
        }
        print(json.dumps(metrics), flush=True)
        scheduler.step(val_metrics[0])

        if val_metrics[1] > best_accuracy:
            best_accuracy = val_metrics[1]
            stale_epochs = 0
            torch.save(
                {"model": model.state_dict(), "config": config, "metrics": metrics},
                output_dir / "best.pt",
            )
        else:
            stale_epochs += 1
            if stale_epochs >= training["early_stopping_patience"]:
                print("Early stopping.", flush=True)
                break


if __name__ == "__main__":
    main()
