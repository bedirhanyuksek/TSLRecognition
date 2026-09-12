from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions


def read_manifest(path: Path) -> list[tuple[str, int]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [(row[0], int(row[1])) for row in csv.reader(handle)]


def sampled_frames(path: Path, count: int) -> list[tuple[int, np.ndarray]]:
    capture = cv2.VideoCapture(str(path))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    if frame_count <= 0:
        capture.release()
        raise RuntimeError(f"Could not read video: {path}")

    frames: list[tuple[int, np.ndarray]] = []
    for frame_index in np.linspace(0, frame_count - 1, count).astype(int):
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
        ok, frame = capture.read()
        if not ok:
            capture.release()
            raise RuntimeError(f"Could not decode frame {frame_index}: {path}")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        timestamp_ms = round(frame_index * 1000.0 / fps)
        frames.append((timestamp_ms, rgb))
    capture.release()
    return frames


def normalized_landmarks(
    landmarks: list,
    count: int,
    include_visibility: bool = False,
) -> tuple[np.ndarray, bool]:
    dimensions = 4 if include_visibility else 3
    values = np.full((count, dimensions), np.nan, dtype=np.float32)
    if not landmarks:
        return values, False

    for index, landmark in enumerate(landmarks[:count]):
        values[index, :3] = (landmark.x, landmark.y, landmark.z)
        if include_visibility:
            values[index, 3] = landmark.visibility or 0.0
    return values, True


def extract_video(
    landmarker: vision.HolisticLandmarker,
    video_path: Path,
    num_frames: int,
    timestamp_offset_ms: int,
) -> dict[str, np.ndarray]:
    frames = [frame for _, frame in sampled_frames(video_path, num_frames)]
    return extract_frames(landmarker, frames, timestamp_offset_ms)


def extract_frames(
    landmarker: vision.HolisticLandmarker,
    frames: list[np.ndarray],
    timestamp_offset_ms: int,
) -> dict[str, np.ndarray]:
    pose_frames: list[np.ndarray] = []
    left_hand_frames: list[np.ndarray] = []
    right_hand_frames: list[np.ndarray] = []
    face_frames: list[np.ndarray] = []
    masks: list[tuple[bool, bool, bool, bool]] = []

    for sequence_index, frame in enumerate(frames):
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = landmarker.detect_for_video(
            image,
            timestamp_offset_ms + sequence_index * 33,
        )
        pose, has_pose = normalized_landmarks(
            result.pose_landmarks, 33, include_visibility=True
        )
        left_hand, has_left_hand = normalized_landmarks(
            result.left_hand_landmarks, 21
        )
        right_hand, has_right_hand = normalized_landmarks(
            result.right_hand_landmarks, 21
        )
        face, has_face = normalized_landmarks(result.face_landmarks, 478)
        pose_frames.append(pose)
        left_hand_frames.append(left_hand)
        right_hand_frames.append(right_hand)
        face_frames.append(face)
        masks.append((has_pose, has_left_hand, has_right_hand, has_face))

    return {
        "pose": np.stack(pose_frames),
        "left_hand": np.stack(left_hand_frames),
        "right_hand": np.stack(right_hand_frames),
        "face": np.stack(face_frames),
        "detected": np.asarray(masks, dtype=np.bool_),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--video-dir", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    samples = read_manifest(args.manifest)
    if args.limit is not None:
        samples = samples[: args.limit]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    options = vision.HolisticLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(args.model)),
        running_mode=vision.RunningMode.VIDEO,
        min_face_detection_confidence=0.4,
        min_face_landmarks_confidence=0.4,
        min_pose_detection_confidence=0.4,
        min_pose_landmarks_confidence=0.4,
        min_hand_landmarks_confidence=0.35,
    )

    started = time.monotonic()
    detection_totals = np.zeros(4, dtype=np.int64)
    frame_total = 0
    completed = 0
    with vision.HolisticLandmarker.create_from_options(options) as landmarker:
        for position, (sample_id, label) in enumerate(samples, start=1):
            output_path = args.output_dir / f"{sample_id}.npz"
            if output_path.exists() and not args.overwrite:
                continue
            video_path = args.video_dir / f"{sample_id}_color.mp4"
            arrays = extract_video(
                landmarker,
                video_path,
                args.frames,
                timestamp_offset_ms=position * 1_000_000,
            )
            np.savez_compressed(
                output_path,
                sample_id=sample_id,
                label=np.int64(label),
                **arrays,
            )
            detection_totals += arrays["detected"].sum(axis=0)
            frame_total += args.frames
            completed += 1
            if position % 10 == 0 or position == len(samples):
                elapsed = time.monotonic() - started
                print(
                    json.dumps(
                        {
                            "completed": position,
                            "total": len(samples),
                            "videos_per_minute": (
                                completed * 60.0 / elapsed if elapsed else 0.0
                            ),
                        }
                    ),
                    flush=True,
                )

    if frame_total:
        rates = detection_totals / frame_total
        print(
            json.dumps(
                {
                    "pose_detection_rate": rates[0],
                    "left_hand_detection_rate": rates[1],
                    "right_hand_detection_rate": rates[2],
                    "face_detection_rate": rates[3],
                }
            )
        )


if __name__ == "__main__":
    main()
