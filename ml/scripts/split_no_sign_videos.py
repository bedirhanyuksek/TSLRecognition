#!/usr/bin/env python3
"""Split long no-sign recordings into fixed-duration training clips."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2


VIDEO_EXTENSIONS = {".avi", ".m4v", ".mov", ".mp4", ".webm"}


def split_video(source: Path, output_dir: Path, seconds: float) -> int:
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise RuntimeError(f"Video açılamadı: {source}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames_per_clip = max(1, round(fps * seconds))
    source_dir = output_dir / source.stem
    source_dir.mkdir(parents=True, exist_ok=True)

    writer: cv2.VideoWriter | None = None
    frames_in_clip = 0
    clip_index = 0
    output_path: Path | None = None

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            if writer is None:
                output_path = source_dir / f"{source.stem}_{clip_index:04d}.mp4"
                writer = cv2.VideoWriter(
                    str(output_path),
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    fps,
                    (width, height),
                )
                if not writer.isOpened():
                    raise RuntimeError(f"Video yazılamadı: {output_path}")

            writer.write(frame)
            frames_in_clip += 1

            if frames_in_clip == frames_per_clip:
                writer.release()
                writer = None
                frames_in_clip = 0
                clip_index += 1
                output_path = None
    finally:
        capture.release()
        if writer is not None:
            writer.release()

    # Eğitim örneklerinin süresi eşit kalsın; kısa son parçayı kaldır.
    if frames_in_clip and output_path is not None:
        output_path.unlink(missing_ok=True)

    return clip_index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("no_sign"))
    parser.add_argument("--output", type=Path, default=Path("no_sign/clips"))
    parser.add_argument("--seconds", type=float, default=2.0)
    args = parser.parse_args()

    sources = sorted(
        path
        for path in args.input.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )
    if not sources:
        raise SystemExit(f"Kaynak video bulunamadı: {args.input}")

    args.output.mkdir(parents=True, exist_ok=True)
    total = 0

    for source in sources:
        count = split_video(source, args.output, args.seconds)
        total += count
        print(f"{source.name}: {count} klip")

    print(f"Toplam: {total} klip")


if __name__ == "__main__":
    main()
