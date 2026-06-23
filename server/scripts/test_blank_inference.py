from __future__ import annotations

import json

import cv2
import numpy as np

from app.config import get_settings
from app.predictor import TIDPredictor


def main() -> None:
    settings = get_settings()
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if not ok:
        raise RuntimeError("Could not encode test image")

    predictor = TIDPredictor(
        word_model_path=settings.word_model_path,
        sign_gate_model_path=settings.sign_gate_model_path,
        class_names_path=settings.class_names_path,
        holistic_model_path=settings.holistic_model_path,
    )
    try:
        result = predictor.predict_image_bytes(bytes(encoded))
    finally:
        predictor.close()
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
