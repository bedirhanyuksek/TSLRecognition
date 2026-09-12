from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class QualityThresholds:
    confidence: float = 0.45
    confidence_margin: float = 0.15
    motion_score: float = 0.025
    pose_detection_rate: float = 0.7
    hand_detection_rate: float = 0.35


def landmark_motion_score(
    pose: np.ndarray,
    left_hand: np.ndarray,
    right_hand: np.ndarray,
) -> float:
    if pose.shape[0] < 2:
        return 0.0

    pose_xyz = pose[:, :, :3]
    shoulders = pose_xyz[:, [11, 12]]
    shoulder_scale = np.linalg.norm(
        shoulders[:, 0, :2] - shoulders[:, 1, :2],
        axis=1,
    )
    valid_scale = np.isfinite(shoulder_scale) & (shoulder_scale > 1e-4)
    fallback_scale = (
        float(np.nanmedian(shoulder_scale[valid_scale]))
        if valid_scale.any()
        else 1.0
    )
    shoulder_scale = np.where(
        valid_scale,
        shoulder_scale,
        fallback_scale,
    )

    tracked_points = np.concatenate(
        (pose_xyz[:, 11:23], left_hand, right_hand),
        axis=1,
    )
    deltas = tracked_points[1:, :, :2] - tracked_points[:-1, :, :2]
    valid_points = np.isfinite(deltas).all(axis=2)
    distances = np.linalg.norm(np.nan_to_num(deltas), axis=2)
    distances = distances / shoulder_scale[1:, None]
    valid_counts = valid_points.sum(axis=1)
    frame_motion = np.divide(
        (distances * valid_points).sum(axis=1),
        valid_counts,
        out=np.zeros(distances.shape[0], dtype=np.float32),
        where=valid_counts > 0,
    )
    return float(np.quantile(frame_motion, 0.75))


def evaluate_prediction_quality(
    *,
    best_confidence: float,
    second_confidence: float,
    detection_rates: np.ndarray,
    motion_score: float,
    thresholds: QualityThresholds,
) -> tuple[bool, float, list[str]]:
    confidence_margin = best_confidence - second_confidence
    rejection_reasons: list[str] = []

    if best_confidence < thresholds.confidence:
        rejection_reasons.append("low_confidence")
    if confidence_margin < thresholds.confidence_margin:
        rejection_reasons.append("ambiguous_prediction")
    if float(detection_rates[0]) < thresholds.pose_detection_rate:
        rejection_reasons.append("pose_not_visible")
    if (
        max(float(detection_rates[1]), float(detection_rates[2]))
        < thresholds.hand_detection_rate
    ):
        rejection_reasons.append("hands_not_visible")
    if motion_score < thresholds.motion_score:
        rejection_reasons.append("insufficient_motion")

    return not rejection_reasons, confidence_margin, rejection_reasons
