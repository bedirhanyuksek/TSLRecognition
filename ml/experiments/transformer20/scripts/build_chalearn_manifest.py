import argparse
import csv
from pathlib import Path

import pandas as pd


def read_labels(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None)
    if df.shape[1] < 2:
        raise SystemExit("Label dosyasi en az iki kolon icermeli: sample_id,label")
    df = df.iloc[:, :2]
    df.columns = ["sample_id", "label"]
    df["sample_id"] = df["sample_id"].astype(str).str.strip()
    df["label"] = df["label"].astype(str).str.strip()
    return df


def class_map(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    df = pd.read_csv(path)
    if "ClassId" in df.columns and "TR" in df.columns:
        return {str(row.ClassId).strip(): str(row.TR).strip() for row in df.itertuples(index=False)}
    df = pd.read_csv(path, header=None)
    mapping = {}
    for row in df.itertuples(index=False):
        class_id = str(row[0]).strip()
        turkish = str(row[1]).strip() if len(row) > 1 else class_id
        mapping[class_id] = turkish
    return mapping


def attach_video_paths(labels: pd.DataFrame, video_root: Path, split: str, mapping: dict[str, str]) -> pd.DataFrame:
    rows = []
    missing = []
    for row in labels.itertuples(index=False):
        sample_id = str(row.sample_id)
        label_id = str(row.label)
        video_path = video_root / f"{sample_id}_color.mp4"
        if not video_path.exists():
            matches = list(video_root.rglob(f"{sample_id}_color.mp4"))
            if matches:
                video_path = matches[0]
            else:
                missing.append(sample_id)
                continue
        rows.append(
            {
                "video_path": str(video_path),
                "label": mapping.get(label_id, label_id),
                "split": split,
                "sample_id": sample_id,
                "label_id": label_id,
            }
        )
    if missing:
        print(f"Uyari: {len(missing)} video bulunamadi. Ilk eksikler: {missing[:5]}")
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-root", type=Path, required=True)
    parser.add_argument("--train-labels", type=Path, required=True)
    parser.add_argument("--val-root", type=Path)
    parser.add_argument("--val-labels", type=Path)
    parser.add_argument("--class-ids", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/manifests/autsl_chalearn_manifest.csv"))
    parser.add_argument("--max-classes", type=int)
    args = parser.parse_args()

    mapping = class_map(args.class_ids)
    frames = [attach_video_paths(read_labels(args.train_labels), args.train_root, "train", mapping)]
    if args.val_root and args.val_labels:
        frames.append(attach_video_paths(read_labels(args.val_labels), args.val_root, "val", mapping))

    df = pd.concat(frames, ignore_index=True)
    if args.max_classes:
        labels = sorted(df["label"].unique())[: args.max_classes]
        df = df[df["label"].isin(labels)].copy()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Manifest yazildi: {args.out} ({len(df)} video, {df['label'].nunique()} sinif)")


if __name__ == "__main__":
    main()
