from __future__ import annotations

import csv
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


POSE_INDICES = np.arange(23)
FACE_INDICES = np.asarray(
    [
        1,
        33,
        61,
        63,
        66,
        70,
        84,
        91,
        105,
        107,
        133,
        146,
        168,
        181,
        263,
        291,
        293,
        296,
        300,
        314,
        321,
        334,
        336,
        362,
        375,
        405,
    ]
)


def read_manifest(path: Path) -> list[tuple[str, int]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [(row[0], int(row[1])) for row in csv.reader(handle)]


def normalize_coordinates(
    coordinates: np.ndarray,
    center: np.ndarray,
    scale: np.ndarray,
) -> np.ndarray:
    return (coordinates - center[:, None, :]) / scale[:, None, None]


def landmark_features_from_arrays(
    pose: np.ndarray,
    left_hand: np.ndarray,
    right_hand: np.ndarray,
    face: np.ndarray,
    detected: np.ndarray,
) -> np.ndarray:
    pose_xyz = pose[:, POSE_INDICES, :3]
    pose_visibility = pose[:, POSE_INDICES, 3]
    face_xyz = face[:, FACE_INDICES, :3]

    shoulders = pose[:, [11, 12], :3]
    shoulder_counts = np.isfinite(shoulders).sum(axis=1)
    shoulder_sums = np.nansum(shoulders, axis=1)
    center = np.divide(
        shoulder_sums,
        shoulder_counts,
        out=np.full_like(shoulder_sums, 0.5),
        where=shoulder_counts > 0,
    )
    scale = np.linalg.norm(shoulders[:, 0, :2] - shoulders[:, 1, :2], axis=1)
    valid_scale = np.isfinite(scale) & (scale > 1e-4)
    fallback_scale = np.nanmedian(scale[valid_scale]) if valid_scale.any() else 1.0
    scale = np.where(valid_scale, scale, fallback_scale).astype(np.float32)
    center = np.nan_to_num(center, nan=0.5)

    groups = [
        normalize_coordinates(pose_xyz, center, scale),
        normalize_coordinates(left_hand, center, scale),
        normalize_coordinates(right_hand, center, scale),
        normalize_coordinates(face_xyz, center, scale),
    ]
    flattened = [group.reshape(group.shape[0], -1) for group in groups]
    features = np.concatenate(
        flattened + [pose_visibility, detected],
        axis=1,
    )
    return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)


def landmark_features(path: Path) -> np.ndarray:
    with np.load(path) as data:
        return landmark_features_from_arrays(
            pose=data["pose"].astype(np.float32),
            left_hand=data["left_hand"].astype(np.float32),
            right_hand=data["right_hand"].astype(np.float32),
            face=data["face"].astype(np.float32),
            detected=data["detected"].astype(np.float32),
        )


def motion_gate_features_from_arrays(
    pose: np.ndarray,
    left_hand: np.ndarray,
    right_hand: np.ndarray,
    detected: np.ndarray,
) -> np.ndarray:
    """Identity-light features based on upper-body motion, not face appearance."""
    pose_xyz = pose[:, 11:23, :3]
    shoulders = pose[:, [11, 12], :3]
    shoulder_counts = np.isfinite(shoulders).sum(axis=1)
    shoulder_sums = np.nansum(shoulders, axis=1)
    center = np.divide(
        shoulder_sums,
        shoulder_counts,
        out=np.full_like(shoulder_sums, 0.5),
        where=shoulder_counts > 0,
    )
    scale = np.linalg.norm(shoulders[:, 0, :2] - shoulders[:, 1, :2], axis=1)
    valid_scale = np.isfinite(scale) & (scale > 1e-4)
    fallback_scale = np.nanmedian(scale[valid_scale]) if valid_scale.any() else 1.0
    scale = np.where(valid_scale, scale, fallback_scale).astype(np.float32)
    center = np.nan_to_num(center, nan=0.5)

    normalized_pose = normalize_coordinates(pose_xyz, center, scale)
    normalized_left = normalize_coordinates(left_hand, center, scale)
    normalized_right = normalize_coordinates(right_hand, center, scale)
    tracked = np.concatenate(
        (normalized_pose, normalized_left, normalized_right),
        axis=1,
    )
    tracked = np.nan_to_num(tracked, nan=0.0, posinf=0.0, neginf=0.0)

    velocity = np.diff(tracked, axis=0, prepend=tracked[:1])
    acceleration = np.diff(velocity, axis=0, prepend=velocity[:1])
    speed = np.linalg.norm(velocity, axis=2)

    # Only coarse positions are retained. They describe the signing space but
    # avoid face landmarks and detailed static body/hand geometry.
    pose_anchor_indices = np.asarray([2, 3, 4, 5])  # elbows and wrists
    hand_anchor_indices = np.asarray([0, 4, 8, 12, 16, 20])
    coarse_positions = np.concatenate(
        (
            normalized_pose[:, pose_anchor_indices],
            normalized_left[:, hand_anchor_indices],
            normalized_right[:, hand_anchor_indices],
        ),
        axis=1,
    )

    features = np.concatenate(
        (
            velocity.reshape(velocity.shape[0], -1),
            acceleration.reshape(acceleration.shape[0], -1),
            speed,
            coarse_positions.reshape(coarse_positions.shape[0], -1),
            detected[:, :3].astype(np.float32),
        ),
        axis=1,
    )
    return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)


def mirrored_landmark_arrays(
    pose: np.ndarray,
    left_hand: np.ndarray,
    right_hand: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mirrored_pose = pose.copy()
    mirrored_pose[:, :, 0] = 1.0 - mirrored_pose[:, :, 0]
    swap_pairs = (
        (1, 4),
        (2, 5),
        (3, 6),
        (7, 8),
        (9, 10),
        (11, 12),
        (13, 14),
        (15, 16),
        (17, 18),
        (19, 20),
        (21, 22),
        (23, 24),
        (25, 26),
        (27, 28),
        (29, 30),
        (31, 32),
    )
    for left_index, right_index in swap_pairs:
        mirrored_pose[:, [left_index, right_index]] = mirrored_pose[
            :, [right_index, left_index]
        ]

    mirrored_left = right_hand.copy()
    mirrored_right = left_hand.copy()
    mirrored_left[:, :, 0] = 1.0 - mirrored_left[:, :, 0]
    mirrored_right[:, :, 0] = 1.0 - mirrored_right[:, :, 0]
    return mirrored_pose, mirrored_left, mirrored_right


def motion_gate_features(path: Path, mirror: bool = False) -> np.ndarray:
    with np.load(path) as data:
        pose = data["pose"].astype(np.float32)
        left_hand = data["left_hand"].astype(np.float32)
        right_hand = data["right_hand"].astype(np.float32)
        if mirror:
            pose, left_hand, right_hand = mirrored_landmark_arrays(
                pose,
                left_hand,
                right_hand,
            )
        return motion_gate_features_from_arrays(
            pose=pose,
            left_hand=left_hand,
            right_hand=right_hand,
            detected=data["detected"].astype(np.float32),
        )


class LandmarkDataset(Dataset):
    def __init__(
        self,
        manifest: Path,
        landmark_dir: Path,
        limit: int | None = None,
        feature_mode: str = "full",
    ) -> None:
        self.samples = read_manifest(manifest)
        self.landmark_dir = landmark_dir
        self.feature_mode = feature_mode
        if limit is not None:
            self.samples = self.samples[:limit]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        sample_id, label = self.samples[index]
        path = self.landmark_dir / f"{sample_id}.npz"
        if not path.is_file():
            raise FileNotFoundError(path)
        if self.feature_mode in {"motion_gate", "motion_gate_augmented"}:
            features = motion_gate_features(
                path,
                mirror=(
                    self.feature_mode == "motion_gate_augmented"
                    and random.random() < 0.5
                ),
            )
        else:
            features = landmark_features(path)
        return (
            torch.from_numpy(features).float(),
            torch.tensor(label, dtype=torch.long),
        )
