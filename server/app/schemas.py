from __future__ import annotations

from pydantic import BaseModel


class ModelStatus(BaseModel):
    word_model: bool
    sign_gate: bool
    class_names: bool
    holistic_model: bool


class HealthResponse(BaseModel):
    ok: bool
    models: ModelStatus


class TopPrediction(BaseModel):
    gloss: str
    display: str
    confidence: float


class ImagePredictionResponse(BaseModel):
    hasSign: bool
    gloss: str | None
    display: str | None
    confidence: float
    top5: list[TopPrediction]
    error: str | None = None
    debug: dict | None = None


class FramePredictionResponse(ImagePredictionResponse):
    frameCount: int
