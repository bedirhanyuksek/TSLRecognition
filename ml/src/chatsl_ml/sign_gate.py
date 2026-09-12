from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from chatsl_ml.landmark_model import LandmarkTCN


class SignGate:
    """Binary temporal classifier: class 0=no sign, class 1=sign."""

    def __init__(
        self,
        checkpoint_path: Path,
        device: torch.device,
        threshold: float = 0.3,
    ) -> None:
        checkpoint = torch.load(
            checkpoint_path,
            map_location="cpu",
            weights_only=False,
        )
        config = checkpoint["config"]
        if int(config["num_classes"]) != 2:
            raise ValueError("Sign gate checkpoint must have two classes")

        self.threshold = threshold
        self.device = device
        input_size = int(
            checkpoint["model"]["input_projection.0.weight"].numel()
        )
        self.model = LandmarkTCN(
            input_size=input_size,
            hidden_size=config["model"]["hidden_size"],
            num_classes=2,
            dropout=config["model"]["dropout"],
        )
        self.model.load_state_dict(checkpoint["model"])
        self.model.to(device).eval()

    def predict(self, features: np.ndarray) -> dict[str, float | bool]:
        with torch.no_grad():
            probabilities = torch.softmax(
                self.model(
                    torch.from_numpy(features)
                    .float()
                    .unsqueeze(0)
                    .to(self.device)
                ),
                dim=1,
            )[0]
        no_sign_probability = float(probabilities[0].item())
        sign_probability = float(probabilities[1].item())
        return {
            "accepted": sign_probability >= self.threshold,
            "sign_probability": sign_probability,
            "no_sign_probability": no_sign_probability,
            "threshold": self.threshold,
        }
