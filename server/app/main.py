from __future__ import annotations

from fastapi import FastAPI, File, UploadFile

from .config import get_settings
from .schemas import HealthResponse, ImagePredictionResponse, ModelStatus

app = FastAPI(title="TID Sign Inference Backend", version="0.1.0")


def model_status() -> ModelStatus:
    settings = get_settings()
    return ModelStatus(
        word_model=settings.word_model_path.is_file(),
        sign_gate=settings.sign_gate_model_path.is_file(),
        class_names=settings.class_names_path.is_file(),
        holistic_model=settings.holistic_model_path.is_file(),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    status = model_status()
    return HealthResponse(
        ok=True,
        models=status,
    )


@app.post("/predict/image", response_model=ImagePredictionResponse)
async def predict_image(
    image: UploadFile = File(...),
) -> ImagePredictionResponse:
    await image.read()
    return ImagePredictionResponse(
        hasSign=False,
        gloss=None,
        display=None,
        confidence=0.0,
        top5=[],
        error="Inference pipeline is not wired yet.",
    )
