from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset


def load_labels(path: Path) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            if len(row) != 2:
                raise ValueError(f"Expected two columns in {path}, got: {row}")
            rows.append((row[0].strip(), int(row[1])))
    return rows


class SignVideoDataset(Dataset):
    def __init__(
        self,
        video_dir: Path,
        labels_path: Path,
        num_frames: int,
        image_size: int,
        modality: str = "color",
        training: bool = False,
        limit: int | None = None,
    ) -> None:
        if modality not in {"color", "depth"}:
            raise ValueError("modality must be 'color' or 'depth'")

        self.video_dir = video_dir
        self.samples = load_labels(labels_path)
        self.num_frames = num_frames
        self.image_size = image_size
        self.modality = modality
        self.training = training
        if limit is not None:
            self.samples = self.samples[:limit]

    def __len__(self) -> int:
        return len(self.samples)

    def _read_frames(self, path: Path) -> np.ndarray:
        capture = cv2.VideoCapture(str(path))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count <= 0:
            capture.release()
            raise RuntimeError(f"Could not read video metadata: {path}")

        indices = np.linspace(0, frame_count - 1, self.num_frames).astype(int)
        frames: list[np.ndarray] = []
        for index in indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
            ok, frame = capture.read()
            if not ok:
                capture.release()
                raise RuntimeError(f"Could not decode frame {index} from {path}")
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(
                frame,
                (self.image_size, self.image_size),
                interpolation=cv2.INTER_AREA,
            )
            frames.append(frame)
        capture.release()
        return np.stack(frames)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        sample_id, label = self.samples[index]
        path = self.video_dir / f"{sample_id}_{self.modality}.mp4"
        if not path.is_file():
            raise FileNotFoundError(path)

        frames = self._read_frames(path)
        tensor = torch.from_numpy(frames).float().permute(0, 3, 1, 2) / 255.0
        mean = torch.tensor((0.485, 0.456, 0.406)).view(1, 3, 1, 1)
        std = torch.tensor((0.229, 0.224, 0.225)).view(1, 3, 1, 1)
        tensor = ((tensor - mean) / std).contiguous()
        return tensor, torch.tensor(label, dtype=torch.long)
