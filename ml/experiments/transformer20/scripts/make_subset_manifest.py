import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--classes", type=int, default=5)
    parser.add_argument("--train-per-class", type=int, default=25)
    parser.add_argument("--val-per-class", type=int, default=8)
    args = parser.parse_args()

    df = pd.read_csv(args.manifest)
    labels = sorted(df["label"].unique())[: args.classes]
    parts = []
    for label in labels:
        label_df = df[df["label"] == label]
        train = label_df[label_df["split"] == "train"].head(args.train_per_class)
        val = label_df[label_df["split"] == "val"].head(args.val_per_class)
        parts.extend([train, val])
    subset = pd.concat(parts, ignore_index=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    subset.to_csv(args.out, index=False)
    print(
        f"Subset yazildi: {args.out} "
        f"({len(subset)} video, {subset['label'].nunique()} sinif)"
    )
    print(subset.groupby(["split", "label"]).size())


if __name__ == "__main__":
    main()
