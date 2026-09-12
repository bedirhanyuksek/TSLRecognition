from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
import yaml
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

from chatsl_ml.data import SignVideoDataset
from chatsl_ml.model import build_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--overfit-samples", type=int)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    return parser.parse_args()


def select_device(requested: str = "auto") -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


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

    for videos, labels in loader:
        videos = videos.to(device).contiguous()
        labels = labels.to(device).contiguous()
        with torch.set_grad_enabled(training):
            logits = model(videos)
            loss = criterion(logits, labels)
            if training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                if gradient_clip_norm is not None:
                    nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
                optimizer.step()

        total_loss += loss.item() * labels.size(0)
        total_correct += (logits.argmax(dim=1) == labels).sum().item()
        top5 = logits.topk(k=5, dim=1).indices
        total_top5_correct += top5.eq(labels.view(-1, 1)).any(dim=1).sum().item()
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

    seed = config["seed"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    root = Path.cwd()
    data_config = config["data"]
    training_config = config["training"]
    limit = args.overfit_samples or (8 if args.smoke_test else None)

    train_dataset = SignVideoDataset(
        root / data_config["train_dir"],
        root / data_config["train_labels"],
        data_config["num_frames"],
        data_config["image_size"],
        data_config["modality"],
        training=True,
        limit=limit,
    )
    val_dir = data_config["val_dir"]
    val_labels = data_config["val_labels"]
    if args.overfit_samples:
        val_dir = data_config["train_dir"]
        val_labels = data_config["train_labels"]
    val_dataset = SignVideoDataset(
        root / val_dir,
        root / val_labels,
        data_config["num_frames"],
        data_config["image_size"],
        data_config["modality"],
        limit=limit,
    )
    batch_size = 2 if args.smoke_test else training_config["batch_size"]
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=training_config["num_workers"],
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        num_workers=training_config["num_workers"],
    )

    model_config = config["model"]
    if args.smoke_test:
        model_config = {**model_config, "pretrained": False}
    model = build_model(model_config, config["num_classes"])
    device = select_device(args.device)
    model.to(device)
    backbone_parameters = [
        parameter
        for name, parameter in model.named_parameters()
        if parameter.requires_grad and name.startswith("features.")
    ]
    head_parameters = [
        parameter
        for name, parameter in model.named_parameters()
        if parameter.requires_grad and not name.startswith("features.")
    ]
    parameter_groups = [{"params": head_parameters, "lr": training_config["learning_rate"]}]
    if backbone_parameters:
        parameter_groups.append(
            {
                "params": backbone_parameters,
                "lr": training_config.get(
                    "backbone_learning_rate", training_config["learning_rate"]
                ),
            }
        )
    optimizer = AdamW(
        parameter_groups,
        weight_decay=training_config["weight_decay"],
    )
    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=training_config.get("lr_factor", 0.5),
        patience=training_config.get("lr_patience", 2),
        min_lr=training_config.get("min_learning_rate", 1e-6),
    )
    criterion = nn.CrossEntropyLoss()
    epochs = args.epochs or (1 if args.smoke_test else training_config["epochs"])
    output_dir = root / training_config["output_dir"]
    if args.overfit_samples:
        output_dir = output_dir.parent / f"{output_dir.name}_overfit"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        json.dumps(
            {
                "device": str(device),
                "model": model_config.get("name", "temporal_cnn"),
                "train_samples": len(train_dataset),
                "val_samples": len(val_dataset),
                "epochs": epochs,
                "trainable_parameters": sum(
                    parameter.numel()
                    for parameter in model.parameters()
                    if parameter.requires_grad
                ),
                "backbone_learning_rate": (
                    optimizer.param_groups[1]["lr"]
                    if len(optimizer.param_groups) > 1
                    else None
                ),
            }
        )
    )

    best_accuracy = -1.0
    stale_epochs = 0
    for epoch in range(1, epochs + 1):
        train_loss, train_accuracy, train_top5_accuracy = run_epoch(
            model,
            train_loader,
            criterion,
            device,
            optimizer,
            training_config.get("gradient_clip_norm"),
        )
        with torch.no_grad():
            val_loss, val_accuracy, val_top5_accuracy = run_epoch(
                model, val_loader, criterion, device
            )
        metrics = {
            "epoch": epoch,
            "learning_rate": optimizer.param_groups[0]["lr"],
            "train_loss": train_loss,
            "train_accuracy": train_accuracy,
            "train_top5_accuracy": train_top5_accuracy,
            "val_loss": val_loss,
            "val_accuracy": val_accuracy,
            "val_top5_accuracy": val_top5_accuracy,
        }
        print(json.dumps(metrics))
        scheduler.step(val_loss)

        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            stale_epochs = 0
            torch.save(
                {"model": model.state_dict(), "config": config, "metrics": metrics},
                output_dir / "best.pt",
            )
        else:
            stale_epochs += 1
            if stale_epochs >= training_config["early_stopping_patience"]:
                print("Early stopping.")
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
