import argparse
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from tqdm import tqdm


POSE_IDS = [0, 11, 12, 13, 14, 15, 16, 23, 24]


def flatten_landmarks(landmarks, count: int) -> list[float]:
    if landmarks is None:
        return [0.0] * count * 4
    values = []
    for item in landmarks.landmark:
        values.extend([item.x, item.y, item.z, item.visibility if hasattr(item, "visibility") else 1.0])
    return values


def select_pose(landmarks) -> list[float]:
    if landmarks is None:
        return [0.0] * len(POSE_IDS) * 4
    values = []
    for idx in POSE_IDS:
        item = landmarks.landmark[idx]
        values.extend([item.x, item.y, item.z, item.visibility])
    return values


def resample(sequence: np.ndarray, frames: int) -> np.ndarray:
    if len(sequence) == 0:
        raise ValueError("Bos landmark dizisi")
    if len(sequence) == frames:
        return sequence.astype(np.float32)
    src = np.linspace(0, len(sequence) - 1, num=len(sequence))
    dst = np.linspace(0, len(sequence) - 1, num=frames)
    out = np.stack([np.interp(dst, src, sequence[:, dim]) for dim in range(sequence.shape[1])], axis=1)
    return out.astype(np.float32)


def frame_indices(total_frames: int, frames: int) -> np.ndarray:
    if total_frames <= 0:
        return np.arange(frames)
    return np.linspace(0, max(total_frames - 1, 0), num=frames).astype(int)


def extract_video(video_path: Path, holistic, frames: int) -> np.ndarray:
    cap = cv2.VideoCapture(str(video_path))
    rows = []
    indices = frame_indices(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), frames)
    target_indices = set(int(idx) for idx in indices)
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx not in target_indices:
            frame_idx += 1
            continue
        if frame.shape[1] > 384:
            scale = 384 / frame.shape[1]
            frame = cv2.resize(frame, (384, int(frame.shape[0] * scale)))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = holistic.process(rgb)
        rows.append(
            select_pose(result.pose_landmarks)
            + flatten_landmarks(result.left_hand_landmarks, 21)
            + flatten_landmarks(result.right_hand_landmarks, 21)
        )
        frame_idx += 1
    cap.release()
    if not rows:
        raise ValueError(f"Video okunamadi veya bos: {video_path}")
    return resample(np.asarray(rows, dtype=np.float32), frames)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("data/landmarks"))
    parser.add_argument("--frames", type=int, default=64)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()

    df = pd.read_csv(args.manifest)
    if args.end is not None:
        df = df.iloc[args.start : args.end].reset_index(drop=True)
    elif args.start:
        df = df.iloc[args.start :].reset_index(drop=True)
    if args.limit:
        df = df.head(args.limit)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    mp_holistic = mp.solutions.holistic
    failures = []
    with mp_holistic.Holistic(static_image_mode=False, model_complexity=1) as holistic:
        for row in tqdm(df.itertuples(index=False), total=len(df)):
            video_path = Path(row.video_path)
            out_path = args.out_dir / f"{row.sample_id}.npz"
            if out_path.exists():
                continue
            try:
                landmarks = extract_video(video_path, holistic, args.frames)
                np.savez_compressed(out_path, landmarks=landmarks, label=row.label, split=row.split)
            except Exception as exc:
                failures.append((str(video_path), str(exc)))

    if failures:
        fail_path = args.out_dir / "failures.csv"
        pd.DataFrame(failures, columns=["video_path", "error"]).to_csv(fail_path, index=False)
        print(f"{len(failures)} video islenemedi. Detay: {fail_path}")


if __name__ == "__main__":
    main()
