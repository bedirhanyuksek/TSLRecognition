import argparse
import json
from pathlib import Path

import pandas as pd
import torch
from sklearn.metrics import accuracy_score
from torch import nn
from torch.utils.data import DataLoader

from datasets.landmark_dataset import LandmarkDataset
from models.landmark_transformer import LandmarkTransformer


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def run_epoch(model, loader, criterion, optimizer, device):
    train = optimizer is not None
    model.train(train)
    losses, preds, targets = [], [], []
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        with torch.set_grad_enabled(train):
            logits = model(x)
            loss = criterion(logits, y)
            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        losses.append(loss.item())
        preds.extend(logits.argmax(dim=1).detach().cpu().tolist())
        targets.extend(y.detach().cpu().tolist())
    return sum(losses) / max(len(losses), 1), accuracy_score(targets, preds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--landmark-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--out", type=Path, default=Path("models/autsl_transformer.pt"))
    args = parser.parse_args()

    df = pd.read_csv(args.manifest)
    labels = sorted(df["label"].astype(str).unique())
    label_to_id = {label: idx for idx, label in enumerate(labels)}
    train_ds = LandmarkDataset(args.manifest, args.landmark_dir, "train", label_to_id)
    val_split = "val" if "val" in set(df["split"].astype(str).str.lower()) else "test"
    val_ds = LandmarkDataset(args.manifest, args.landmark_dir, val_split, label_to_id)

    sample_x, _ = train_ds[0]
    device = torch.device(device_name())
    model = LandmarkTransformer(input_dim=sample_x.shape[-1], num_classes=len(labels)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    best_acc = 0.0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, None, device)
        print(
            f"epoch={epoch:03d} train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
        )
        if val_acc >= best_acc:
            best_acc = val_acc
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "label_to_id": label_to_id,
                    "input_dim": sample_x.shape[-1],
                    "frames": sample_x.shape[0],
                },
                args.out,
            )

    meta_path = args.out.with_suffix(".json")
    meta_path.write_text(json.dumps({"best_val_acc": best_acc, "labels": labels}, indent=2), encoding="utf-8")
    print(f"En iyi model: {args.out} val_acc={best_acc:.4f}")


if __name__ == "__main__":
    main()
