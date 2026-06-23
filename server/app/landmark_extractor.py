from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

from .landmark_features import (
    landmark_features_from_arrays,
    motion_gate_features_from_arrays,
)


@dataclass(frozen=True)
class LandmarkBundle:
    arrays: dict[str, np.ndarray]
    word_features: np.ndarray
    gate_features: np.ndarray


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image could not be decoded")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


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


class HolisticFeatureExtractor:
    def __init__(self, model_path: Path, frames_per_window: int = 24) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(model_path)
        self.frames_per_window = frames_per_window
        self.timestamp_offset_ms = 1_000_000
        options = vision.HolisticLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            min_face_detection_confidence=0.4,
            min_face_landmarks_confidence=0.4,
            min_pose_detection_confidence=0.4,
            min_pose_landmarks_confidence=0.4,
            min_hand_landmarks_confidence=0.35,
        )
        self.landmarker = vision.HolisticLandmarker.create_from_options(options)

    def close(self) -> None:
        self.landmarker.close()

    def extract_from_image(self, image: np.ndarray) -> LandmarkBundle:
        frames = [image] * self.frames_per_window
        return self.extract_from_frames(frames)

    def extract_from_frames(self, frames: list[np.ndarray]) -> LandmarkBundle:
        if not frames:
            raise ValueError("At least one frame is required")
        if len(frames) != self.frames_per_window:
            indices = np.linspace(0, len(frames) - 1, self.frames_per_window).astype(int)
            frames = [frames[int(index)] for index in indices]

        arrays = self._extract_arrays(frames)
        detected = arrays["detected"].astype(np.float32)
        word_features = landmark_features_from_arrays(
            pose=arrays["pose"],
            left_hand=arrays["left_hand"],
            right_hand=arrays["right_hand"],
            face=arrays["face"],
            detected=detected,
        )
        gate_features = motion_gate_features_from_arrays(
            pose=arrays["pose"],
            left_hand=arrays["left_hand"],
            right_hand=arrays["right_hand"],
            detected=detected,
        )
        return LandmarkBundle(
            arrays=arrays,
            word_features=word_features,
            gate_features=gate_features,
        )

    def _extract_arrays(self, frames: list[np.ndarray]) -> dict[str, np.ndarray]:
        pose_frames: list[np.ndarray] = []
        left_hand_frames: list[np.ndarray] = []
        right_hand_frames: list[np.ndarray] = []
        face_frames: list[np.ndarray] = []
        masks: list[tuple[bool, bool, bool, bool]] = []

        timestamp_offset_ms = self.timestamp_offset_ms
        self.timestamp_offset_ms += 1_000_000
        for sequence_index, frame in enumerate(frames):
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            result = self.landmarker.detect_for_video(
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
