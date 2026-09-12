#!/usr/bin/env python3
"""Prepare balanced sign/no-sign manifests and lightweight symlink datasets."""

from __future__ import annotations

import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NO_SIGN_CLIPS = ROOT / "no_sign" / "clips"
MANIFEST_DIR = ROOT / "data" / "sign_gate" / "manifests"
VIDEO_DIR = ROOT / "data" / "sign_gate" / "videos"
NO_SIGN_LANDMARK_DIR = ROOT / "data" / "sign_gate" / "no_sign_landmarks"
TRAIN_LANDMARK_DIR = ROOT / "data" / "sign_gate" / "landmarks" / "train"
VAL_LANDMARK_DIR = ROOT / "data" / "sign_gate" / "landmarks" / "val"
TRAIN_SIGN_MANIFEST = ROOT / "data" / "train-data-with-labels" / "train_labels.csv"
VAL_SIGN_MANIFEST = (
    ROOT / "data" / "extracted" / "validation-labels" / "ground_truth.csv"
)
TRAIN_SIGN_LANDMARK_DIR = ROOT / "data" / "landmarks" / "train_full"
VAL_SIGN_LANDMARK_DIR = ROOT / "data" / "landmarks" / "val_full"

TRAIN_RECORDINGS = {
    "bed-3",
    "bedo_1",
    "bedo_2",
    "ibo-1",
    "ibo-2",
    "ibo-3",
}
VAL_RECORDINGS = {"bedo-4", "ibo-4"}


def replace_symlink(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(target.resolve())


def read_manifest(path: Path) -> list[tuple[str, int]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [(row[0], int(row[1])) for row in csv.reader(handle)]


def write_manifest(path: Path, rows: list[tuple[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)


def no_sign_samples(recordings: set[str]) -> list[tuple[str, Path]]:
    samples: list[tuple[str, Path]] = []
    for recording in sorted(recordings):
        for clip in sorted((NO_SIGN_CLIPS / recording).glob("*.mp4")):
            sample_id = f"no_sign_{recording.replace('-', '_')}_{clip.stem.rsplit('_', 1)[-1]}"
            samples.append((sample_id, clip))
    return samples


def choose_sign_samples(
    manifest: Path,
    landmark_dir: Path,
    count: int,
    seed: int,
) -> list[str]:
    candidates = [
        sample_id
        for sample_id, _ in read_manifest(manifest)
        if (landmark_dir / f"{sample_id}.npz").is_file()
    ]
    if len(candidates) < count:
        raise RuntimeError(
            f"{manifest} içinde yalnızca {len(candidates)} hazır landmark var; "
            f"{count} gerekiyor."
        )
    random.Random(seed).shuffle(candidates)
    return candidates[:count]


def prepare_split(
    split: str,
    no_sign: list[tuple[str, Path]],
    sign_manifest: Path,
    sign_landmark_dir: Path,
    output_landmark_dir: Path,
    seed: int,
) -> None:
    sign_samples = choose_sign_samples(
        sign_manifest,
        sign_landmark_dir,
        len(no_sign),
        seed,
    )
    no_sign_rows = [(sample_id, 0) for sample_id, _ in no_sign]
    combined_rows = no_sign_rows + [
        (f"sign_{sample_id}", 1) for sample_id in sign_samples
    ]
    random.Random(seed).shuffle(combined_rows)

    write_manifest(MANIFEST_DIR / f"{split}_no_sign.csv", no_sign_rows)
    write_manifest(MANIFEST_DIR / f"{split}.csv", combined_rows)

    for sample_id, clip in no_sign:
        replace_symlink(VIDEO_DIR / f"{sample_id}_color.mp4", clip)
        extracted = NO_SIGN_LANDMARK_DIR / f"{sample_id}.npz"
        if extracted.is_file():
            replace_symlink(output_landmark_dir / f"{sample_id}.npz", extracted)

    for sample_id in sign_samples:
        replace_symlink(
            output_landmark_dir / f"sign_{sample_id}.npz",
            sign_landmark_dir / f"{sample_id}.npz",
        )

    print(
        f"{split}: {len(no_sign)} no_sign + "
        f"{len(sign_samples)} sign = {len(combined_rows)}"
    )


def main() -> None:
    train_no_sign = no_sign_samples(TRAIN_RECORDINGS)
    val_no_sign = no_sign_samples(VAL_RECORDINGS)
    prepare_split(
        "train",
        train_no_sign,
        TRAIN_SIGN_MANIFEST,
        TRAIN_SIGN_LANDMARK_DIR,
        TRAIN_LANDMARK_DIR,
        seed=42,
    )
    prepare_split(
        "val",
        val_no_sign,
        VAL_SIGN_MANIFEST,
        VAL_SIGN_LANDMARK_DIR,
        VAL_LANDMARK_DIR,
        seed=43,
    )

    print(
        "No-sign landmarkları çıkarıldıktan sonra bu scripti tekrar çalıştırarak "
        "birleşik landmark klasörlerini tamamlayın."
    )


if __name__ == "__main__":
    main()
