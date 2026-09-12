from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from chatsl_ml.landmark_data import LandmarkDataset
from chatsl_ml.landmark_model import LandmarkTCN
from chatsl_ml.train import select_device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--landmarks", type=Path, required=True)
    parser.add_argument("--class-names", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    return parser.parse_args()


def load_class_names(path: Path) -> dict[int, tuple[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {
            int(row["ClassId"]): (row["TR"], row["EN"])
            for row in csv.DictReader(handle)
        }


def signer_from_sample(sample_id: str) -> str:
    return sample_id.split("_sample", maxsplit=1)[0]


def main() -> None:
    args = parse_args()
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    config = checkpoint["config"]
    class_names = load_class_names(args.class_names)
    dataset = LandmarkDataset(args.manifest, args.landmarks)
    loader = DataLoader(dataset, batch_size=args.batch_size, num_workers=0)
    sample_features, _ = dataset[0]
    model = LandmarkTCN(
        input_size=sample_features.shape[1],
        hidden_size=config["model"]["hidden_size"],
        num_classes=config["num_classes"],
        dropout=config["model"]["dropout"],
    )
    model.load_state_dict(checkpoint["model"])
    device = select_device(args.device)
    model.to(device).eval()

    predictions: list[int] = []
    top5_predictions: list[list[int]] = []
    with torch.no_grad():
        for sequences, _ in loader:
            logits = model(sequences.to(device).contiguous())
            predictions.extend(logits.argmax(dim=1).cpu().tolist())
            top5_predictions.extend(logits.topk(k=5, dim=1).indices.cpu().tolist())

    class_total: Counter[int] = Counter()
    class_correct: Counter[int] = Counter()
    class_top5_correct: Counter[int] = Counter()
    signer_total: Counter[str] = Counter()
    signer_correct: Counter[str] = Counter()
    signer_top5_correct: Counter[str] = Counter()
    confusions: Counter[tuple[int, int]] = Counter()
    errors_by_class: dict[int, Counter[int]] = defaultdict(Counter)

    for (sample_id, label), prediction, top5 in zip(
        dataset.samples,
        predictions,
        top5_predictions,
        strict=True,
    ):
        signer = signer_from_sample(sample_id)
        class_total[label] += 1
        signer_total[signer] += 1
        if prediction == label:
            class_correct[label] += 1
            signer_correct[signer] += 1
        else:
            confusions[(label, prediction)] += 1
            errors_by_class[label][prediction] += 1
        if label in top5:
            class_top5_correct[label] += 1
            signer_top5_correct[signer] += 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    class_rows: list[dict] = []
    for class_id in sorted(class_total):
        tr_name, en_name = class_names[class_id]
        most_confused = errors_by_class[class_id].most_common(1)
        confused_id = most_confused[0][0] if most_confused else None
        confused_count = most_confused[0][1] if most_confused else 0
        confused_tr, confused_en = (
            class_names[confused_id] if confused_id is not None else ("", "")
        )
        class_rows.append(
            {
                "class_id": class_id,
                "tr": tr_name,
                "en": en_name,
                "samples": class_total[class_id],
                "top1_accuracy": class_correct[class_id] / class_total[class_id],
                "top5_accuracy": class_top5_correct[class_id] / class_total[class_id],
                "most_confused_class_id": confused_id,
                "most_confused_tr": confused_tr,
                "most_confused_en": confused_en,
                "confusion_count": confused_count,
            }
        )

    with (args.output_dir / "class_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=class_rows[0].keys())
        writer.writeheader()
        writer.writerows(class_rows)

    signer_rows = []
    for signer in sorted(signer_total):
        signer_rows.append(
            {
                "signer": signer,
                "samples": signer_total[signer],
                "top1_accuracy": signer_correct[signer] / signer_total[signer],
                "top5_accuracy": signer_top5_correct[signer] / signer_total[signer],
            }
        )
    with (args.output_dir / "signer_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=signer_rows[0].keys())
        writer.writeheader()
        writer.writerows(signer_rows)

    confusion_rows = []
    for (true_id, predicted_id), count in confusions.most_common():
        true_tr, true_en = class_names[true_id]
        predicted_tr, predicted_en = class_names[predicted_id]
        confusion_rows.append(
            {
                "true_class_id": true_id,
                "true_tr": true_tr,
                "true_en": true_en,
                "predicted_class_id": predicted_id,
                "predicted_tr": predicted_tr,
                "predicted_en": predicted_en,
                "count": count,
            }
        )
    with (args.output_dir / "confusions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=confusion_rows[0].keys())
        writer.writeheader()
        writer.writerows(confusion_rows)

    total = len(dataset)
    summary = {
        "checkpoint_epoch": checkpoint["metrics"]["epoch"],
        "samples": total,
        "top1_accuracy": sum(class_correct.values()) / total,
        "top5_accuracy": sum(class_top5_correct.values()) / total,
        "perfect_classes": sum(row["top1_accuracy"] == 1.0 for row in class_rows),
        "zero_accuracy_classes": sum(row["top1_accuracy"] == 0.0 for row in class_rows),
        "worst_classes": sorted(class_rows, key=lambda row: row["top1_accuracy"])[:15],
        "top_confusions": confusion_rows[:20],
        "signers": signer_rows,
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
