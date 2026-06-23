from __future__ import annotations

import json

import cv2
import numpy as np

from app.config import get_settings
from app.landmark_extractor import HolisticFeatureExtractor


def main() -> None:
    settings = get_settings()
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if not ok:
        raise RuntimeError("Could not encode test image")

    extractor = HolisticFeatureExtractor(settings.holistic_model_path)
    try:
        bundle = extractor.extract_from_image(image)
    finally:
        extractor.close()

    print(
        json.dumps(
            {
                "pose": list(bundle.arrays["pose"].shape),
                "left_hand": list(bundle.arrays["left_hand"].shape),
                "right_hand": list(bundle.arrays["right_hand"].shape),
                "face": list(bundle.arrays["face"].shape),
                "detected": list(bundle.arrays["detected"].shape),
                "word_features": list(bundle.word_features.shape),
                "gate_features": list(bundle.gate_features.shape),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
