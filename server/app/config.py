from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    root_dir: Path = Path(__file__).resolve().parents[1]
    word_model_path: Path = Path(__file__).resolve().parents[1] / "models" / "landmark_tcn_full.pt"
    sign_gate_model_path: Path = Path(__file__).resolve().parents[1] / "models" / "sign_gate.pt"
    class_names_path: Path = Path(__file__).resolve().parents[1] / "models" / "SignList_ClassId_TR_EN.csv"
    holistic_model_path: Path = Path(__file__).resolve().parents[1] / "models" / "holistic_landmarker.task"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
