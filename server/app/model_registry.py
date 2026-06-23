from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from .landmark_model import LandmarkTCN


@dataclass(frozen=True)
class ClassName:
    class_id: int
    tr: str
    en: str


@dataclass(frozen=True)
class LoadedModel:
    model: LandmarkTCN
    config: dict[str, Any]
    metrics: dict[str, Any]
    input_size: int
    num_classes: int


def select_device(requested: str = "auto") -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_class_names(path: Path) -> dict[int, ClassName]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        return {
            int(row["ClassId"]): ClassName(
                class_id=int(row["ClassId"]),
                tr=row["TR"],
                en=row["EN"],
            )
            for row in rows
        }


def load_tcn_checkpoint(path: Path, device: torch.device) -> LoadedModel:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    config = checkpoint["config"]
    state_dict = checkpoint["model"]
    input_size = int(state_dict["input_projection.0.weight"].numel())
    num_classes = int(config["num_classes"])
    model_config = config["model"]
    model = LandmarkTCN(
        input_size=input_size,
        hidden_size=int(model_config["hidden_size"]),
        num_classes=num_classes,
        dropout=float(model_config["dropout"]),
    )
    model.load_state_dict(state_dict)
    model.to(device).eval()
    return LoadedModel(
        model=model,
        config=config,
        metrics=checkpoint.get("metrics", {}),
        input_size=input_size,
        num_classes=num_classes,
    )


def inspect_model_files(
    *,
    word_model_path: Path,
    sign_gate_model_path: Path,
    class_names_path: Path,
    device_name: str = "auto",
) -> dict[str, Any]:
    device = select_device(device_name)
    class_names = load_class_names(class_names_path)
    word_model = load_tcn_checkpoint(word_model_path, device)
    sign_gate = load_tcn_checkpoint(sign_gate_model_path, device)
    return {
        "device": str(device),
        "classes": len(class_names),
        "word_model": {
            "num_classes": word_model.num_classes,
            "input_size": word_model.input_size,
            "metrics": word_model.metrics,
        },
        "sign_gate": {
            "num_classes": sign_gate.num_classes,
            "input_size": sign_gate.input_size,
            "metrics": sign_gate.metrics,
        },
    }
