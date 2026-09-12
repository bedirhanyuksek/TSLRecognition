import argparse
import json
from pathlib import Path

import pandas as pd
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch.utils.data import DataLoader

from datasets.landmark_dataset import LandmarkDataset
from models.landmark_transformer import LandmarkTransformer


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--landmark-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--out", type=Path, default=Path("reports/eval.json"))
    args = parser.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu")
    label_to_id = ckpt["label_to_id"]
    id_to_label = {idx: label for label, idx in label_to_id.items()}
    df = pd.read_csv(args.manifest)
    split = args.split if args.split in set(df["split"].astype(str).str.lower()) else "val"
    ds = LandmarkDataset(args.manifest, args.landmark_dir, split, label_to_id)
    loader = DataLoader(ds, batch_size=64, shuffle=False, num_workers=0)

    device = torch.device(device_name())
    model = LandmarkTransformer(input_dim=ckpt["input_dim"], num_classes=len(label_to_id)).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    preds, targets = [], []
    with torch.no_grad():
        for x, y in loader:
            logits = model(x.to(device))
            preds.extend(logits.argmax(dim=1).cpu().tolist())
            targets.extend(y.tolist())

    target_names = [id_to_label[idx] for idx in range(len(id_to_label))]
    report = {
        "split": split,
        "accuracy": accuracy_score(targets, preds),
        "classification_report": classification_report(targets, preds, target_names=target_names, output_dict=True),
        "confusion_matrix": confusion_matrix(targets, preds).tolist(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"split": split, "accuracy": report["accuracy"], "out": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
