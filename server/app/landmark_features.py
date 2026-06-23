from __future__ import annotations

import numpy as np

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


def motion_gate_features_from_arrays(
    pose: np.ndarray,
    left_hand: np.ndarray,
    right_hand: np.ndarray,
    detected: np.ndarray,
) -> np.ndarray:
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

    pose_anchor_indices = np.asarray([2, 3, 4, 5])
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
