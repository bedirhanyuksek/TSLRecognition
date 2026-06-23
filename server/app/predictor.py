from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .landmark_extractor import HolisticFeatureExtractor, decode_image_bytes
from .model_registry import (
    ClassName,
    LoadedModel,
    load_class_names,
    load_tcn_checkpoint,
    select_device,
)
from .quality import (
    QualityThresholds,
    evaluate_prediction_quality,
    landmark_motion_score,
)
from .schemas import ImagePredictionResponse, TopPrediction


@dataclass(frozen=True)
class PredictorConfig:
    top_k: int = 5
    sign_gate_threshold: float = 0.3
    quality_thresholds: QualityThresholds = field(default_factory=QualityThresholds)


class TIDPredictor:
    def __init__(
        self,
        *,
        word_model_path: Path,
        sign_gate_model_path: Path,
        class_names_path: Path,
        holistic_model_path: Path,
        device_name: str = "auto",
        config: PredictorConfig = PredictorConfig(),
    ) -> None:
        self.device = select_device(device_name)
        self.config = config
        self.class_names = load_class_names(class_names_path)
        self.word_model = load_tcn_checkpoint(word_model_path, self.device)
        self.sign_gate = load_tcn_checkpoint(sign_gate_model_path, self.device)
        self.extractor = HolisticFeatureExtractor(holistic_model_path)
        self._validate()

    def close(self) -> None:
        self.extractor.close()

    def predict_image_bytes(self, image_bytes: bytes) -> ImagePredictionResponse:
        image = decode_image_bytes(image_bytes)
        bundle = self.extractor.extract_from_image(image)
        return self._predict_features(
            word_features=bundle.word_features,
            gate_features=bundle.gate_features,
            arrays=bundle.arrays,
        )

    def predict_frame_bytes(self, frame_bytes: list[bytes]) -> ImagePredictionResponse:
        if not frame_bytes:
            raise ValueError("At least one frame is required")
        frames = [decode_image_bytes(payload) for payload in frame_bytes]
        bundle = self.extractor.extract_from_frames(frames)
        return self._predict_features(
            word_features=bundle.word_features,
            gate_features=bundle.gate_features,
            arrays=bundle.arrays,
        )

    def _predict_features(
        self,
        *,
        word_features: np.ndarray,
        gate_features: np.ndarray,
        arrays: dict[str, np.ndarray],
    ) -> ImagePredictionResponse:
        sign_gate = self._predict_sign_gate(gate_features)
        top_predictions = self._predict_word(word_features)
        best = top_predictions[0]
        second_confidence = top_predictions[1].confidence if len(top_predictions) > 1 else 0.0
        detection_rates = arrays["detected"].astype(np.float32).mean(axis=0)
        motion_score = landmark_motion_score(
            arrays["pose"],
            arrays["left_hand"],
            arrays["right_hand"],
        )
        accepted, confidence_margin, rejection_reasons = evaluate_prediction_quality(
            best_confidence=best.confidence,
            second_confidence=second_confidence,
            detection_rates=detection_rates,
            motion_score=motion_score,
            thresholds=self.config.quality_thresholds,
        )
        if not sign_gate["accepted"]:
            accepted = False
            rejection_reasons = ["no_sign"] + rejection_reasons

        return ImagePredictionResponse(
            hasSign=accepted,
            gloss=best.gloss if accepted else None,
            display=best.display if accepted else None,
            confidence=best.confidence if accepted else 0.0,
            top5=top_predictions,
            error=None if accepted else ",".join(rejection_reasons),
            debug={
                "device": str(self.device),
                "signGate": sign_gate,
                "quality": {
                    "confidenceMargin": confidence_margin,
                    "motionScore": motion_score,
                    "detectionRates": {
                        "pose": float(detection_rates[0]),
                        "leftHand": float(detection_rates[1]),
                        "rightHand": float(detection_rates[2]),
                        "face": float(detection_rates[3]),
                    },
                },
            },
        )

    def _predict_sign_gate(self, features: np.ndarray) -> dict[str, float | bool]:
        probabilities = self._softmax(self.sign_gate, features)
        no_sign_probability = float(probabilities[0])
        sign_probability = float(probabilities[1])
        return {
            "accepted": sign_probability >= self.config.sign_gate_threshold,
            "signProbability": sign_probability,
            "noSignProbability": no_sign_probability,
            "threshold": self.config.sign_gate_threshold,
        }

    def _predict_word(self, features: np.ndarray) -> list[TopPrediction]:
        probabilities = self._softmax(self.word_model, features)
        top_indices = np.argsort(probabilities)[::-1][: self.config.top_k]
        predictions = []
        for class_id in top_indices:
            class_name = self.class_names[int(class_id)]
            predictions.append(
                TopPrediction(
                    gloss=class_name.tr,
                    display=class_name.tr,
                    confidence=float(probabilities[class_id]),
                )
            )
        return predictions

    def _softmax(self, loaded: LoadedModel, features: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            probabilities = torch.softmax(
                loaded.model(
                    torch.from_numpy(features)
                    .float()
                    .unsqueeze(0)
                    .to(self.device)
                ),
                dim=1,
            )[0]
        return probabilities.detach().cpu().numpy()

    def _validate(self) -> None:
        if self.word_model.num_classes != len(self.class_names):
            raise ValueError(
                f"Word model has {self.word_model.num_classes} classes but "
                f"{len(self.class_names)} class labels were loaded"
            )
        if self.word_model.input_size != 300:
            raise ValueError(f"Unexpected word model input size: {self.word_model.input_size}")
        if self.sign_gate.num_classes != 2:
            raise ValueError(f"Unexpected sign gate class count: {self.sign_gate.num_classes}")
        if self.sign_gate.input_size != 429:
            raise ValueError(f"Unexpected sign gate input size: {self.sign_gate.input_size}")

    def model_summary(self) -> dict[str, Any]:
        return {
            "device": str(self.device),
            "classes": len(self.class_names),
            "wordModel": {
                "inputSize": self.word_model.input_size,
                "numClasses": self.word_model.num_classes,
                "metrics": self.word_model.metrics,
            },
            "signGate": {
                "inputSize": self.sign_gate.input_size,
                "numClasses": self.sign_gate.num_classes,
                "metrics": self.sign_gate.metrics,
            },
        }
