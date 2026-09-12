from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

from chatsl_ml.data import load_labels


def load_class_names(path: Path) -> dict[int, tuple[str, str]]:
    names: dict[int, tuple[str, str]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            class_id = int(row["ClassId"])
            names[class_id] = (row["TR"], row["EN"])
    return names


def signer_from_sample(sample_id: str) -> str:
    return sample_id.split("_sample", maxsplit=1)[0]


def read_video_frames(path: Path, count: int = 3) -> list[np.ndarray]:
    capture = cv2.VideoCapture(str(path))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0:
        capture.release()
        raise RuntimeError(f"Could not read video: {path}")

    frames: list[np.ndarray] = []
    for index in np.linspace(0, frame_count - 1, count + 2).astype(int)[1:-1]:
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
        ok, frame = capture.read()
        if not ok:
            capture.release()
            raise RuntimeError(f"Could not decode frame {index}: {path}")
        frames.append(frame)
    capture.release()
    return frames


def fit_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    scale = min(width / frame.shape[1], height / frame.shape[0])
    resized = cv2.resize(
        frame,
        (round(frame.shape[1] * scale), round(frame.shape[0] * scale)),
        interpolation=cv2.INTER_AREA,
    )
    canvas = np.full((height, width, 3), 245, dtype=np.uint8)
    x = (width - resized.shape[1]) // 2
    y = (height - resized.shape[0]) // 2
    canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
    return canvas


def create_contact_sheet(args: argparse.Namespace) -> None:
    labels = load_labels(args.labels)
    class_names = load_class_names(args.class_names)
    by_class: dict[int, list[str]] = defaultdict(list)
    for sample_id, class_id in labels:
        by_class[class_id].append(sample_id)

    rng = random.Random(args.seed)
    selected_classes = sorted(by_class)
    rng.shuffle(selected_classes)
    selected_classes = selected_classes[: args.samples]

    cell_width = args.frame_width * args.frames
    cell_height = args.frame_height + 54
    rows = (len(selected_classes) + args.columns - 1) // args.columns
    sheet = np.full(
        (rows * cell_height, args.columns * cell_width, 3),
        255,
        dtype=np.uint8,
    )

    for position, class_id in enumerate(selected_classes):
        sample_id = rng.choice(by_class[class_id])
        video_path = args.video_dir / f"{sample_id}_color.mp4"
        frames = read_video_frames(video_path, args.frames)
        strip = np.concatenate(
            [fit_frame(frame, args.frame_width, args.frame_height) for frame in frames],
            axis=1,
        )
        row, column = divmod(position, args.columns)
        x = column * cell_width
        y = row * cell_height
        sheet[y : y + args.frame_height, x : x + cell_width] = strip

        tr_name, en_name = class_names[class_id]
        cv2.putText(
            sheet,
            f"{class_id}: {tr_name} / {en_name}",
            (x + 6, y + args.frame_height + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (20, 20, 20),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            sheet,
            sample_id,
            (x + 6, y + args.frame_height + 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (80, 80, 80),
            1,
            cv2.LINE_AA,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), sheet):
        raise RuntimeError(f"Could not write {args.output}")
    print(f"Wrote {len(selected_classes)} samples to {args.output}")


def select_diverse_samples(
    samples: list[str],
    per_class: int,
    rng: random.Random,
) -> list[str]:
    by_signer: dict[str, list[str]] = defaultdict(list)
    for sample_id in samples:
        by_signer[signer_from_sample(sample_id)].append(sample_id)
    for signer_samples in by_signer.values():
        rng.shuffle(signer_samples)

    signers = list(by_signer)
    rng.shuffle(signers)
    selected: list[str] = []
    while len(selected) < per_class:
        added = False
        for signer in signers:
            if by_signer[signer]:
                selected.append(by_signer[signer].pop())
                added = True
                if len(selected) == per_class:
                    break
        if not added:
            break
    return selected


def create_balanced_manifest(args: argparse.Namespace) -> None:
    labels = load_labels(args.labels)
    by_class: dict[int, list[str]] = defaultdict(list)
    for sample_id, class_id in labels:
        by_class[class_id].append(sample_id)

    rng = random.Random(args.seed)
    selected: list[tuple[str, int]] = []
    for class_id in sorted(by_class):
        class_samples = select_diverse_samples(
            by_class[class_id],
            args.per_class,
            rng,
        )
        if len(class_samples) < args.per_class:
            raise ValueError(
                f"Class {class_id} has only {len(class_samples)} selectable samples"
            )
        selected.extend((sample_id, class_id) for sample_id in class_samples)
    rng.shuffle(selected)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(selected)

    signer_count = len({signer_from_sample(sample_id) for sample_id, _ in selected})
    print(
        f"Wrote {len(selected)} samples across {len(by_class)} classes "
        f"and {signer_count} signers to {args.output}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    sheet = subparsers.add_parser("contact-sheet")
    sheet.add_argument("--video-dir", type=Path, required=True)
    sheet.add_argument("--labels", type=Path, required=True)
    sheet.add_argument("--class-names", type=Path, required=True)
    sheet.add_argument("--output", type=Path, required=True)
    sheet.add_argument("--samples", type=int, default=24)
    sheet.add_argument("--frames", type=int, default=3)
    sheet.add_argument("--columns", type=int, default=3)
    sheet.add_argument("--frame-width", type=int, default=180)
    sheet.add_argument("--frame-height", type=int, default=180)
    sheet.add_argument("--seed", type=int, default=42)
    sheet.set_defaults(handler=create_contact_sheet)

    manifest = subparsers.add_parser("balanced-manifest")
    manifest.add_argument("--labels", type=Path, required=True)
    manifest.add_argument("--output", type=Path, required=True)
    manifest.add_argument("--per-class", type=int, default=10)
    manifest.add_argument("--seed", type=int, default=42)
    manifest.set_defaults(handler=create_balanced_manifest)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
