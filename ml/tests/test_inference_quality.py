from __future__ import annotations

import unittest

import numpy as np

from chatsl_ml.inference_quality import (
    QualityThresholds,
    evaluate_prediction_quality,
    landmark_motion_score,
)


def landmark_arrays(frames: int = 24) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pose = np.full((frames, 33, 4), np.nan, dtype=np.float32)
    left_hand = np.full((frames, 21, 3), np.nan, dtype=np.float32)
    right_hand = np.full((frames, 21, 3), np.nan, dtype=np.float32)
    pose[:, 11, :3] = (0.4, 0.5, 0.0)
    pose[:, 12, :3] = (0.6, 0.5, 0.0)
    pose[:, 11:23, 3] = 1.0
    return pose, left_hand, right_hand


class InferenceQualityTests(unittest.TestCase):
    def test_stationary_landmarks_have_zero_motion(self) -> None:
        pose, left_hand, right_hand = landmark_arrays()
        left_hand[:] = (0.45, 0.45, 0.0)

        score = landmark_motion_score(pose, left_hand, right_hand)

        self.assertAlmostEqual(score, 0.0)

    def test_moving_hand_exceeds_default_motion_threshold(self) -> None:
        pose, left_hand, right_hand = landmark_arrays()
        for frame_index in range(left_hand.shape[0]):
            left_hand[frame_index] = (
                0.35 + frame_index * 0.01,
                0.45,
                0.0,
            )

        score = landmark_motion_score(pose, left_hand, right_hand)

        self.assertGreater(score, QualityThresholds().motion_score)

    def test_quality_rejects_ambiguous_stationary_prediction(self) -> None:
        accepted, margin, reasons = evaluate_prediction_quality(
            best_confidence=0.8,
            second_confidence=0.72,
            detection_rates=np.asarray([1.0, 0.8, 0.0, 1.0]),
            motion_score=0.0,
            thresholds=QualityThresholds(),
        )

        self.assertFalse(accepted)
        self.assertAlmostEqual(margin, 0.08)
        self.assertEqual(
            reasons,
            ["ambiguous_prediction", "insufficient_motion"],
        )

    def test_quality_accepts_visible_confident_movement(self) -> None:
        accepted, margin, reasons = evaluate_prediction_quality(
            best_confidence=0.9,
            second_confidence=0.2,
            detection_rates=np.asarray([1.0, 0.8, 0.0, 1.0]),
            motion_score=0.08,
            thresholds=QualityThresholds(),
        )

        self.assertTrue(accepted)
        self.assertAlmostEqual(margin, 0.7)
        self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main()
