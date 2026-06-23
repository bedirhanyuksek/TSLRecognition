from __future__ import annotations

from functools import lru_cache

from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile

from .config import get_settings
from .predictor import TIDPredictor
from .schemas import FramePredictionResponse, HealthResponse, ImagePredictionResponse, ModelStatus

app = FastAPI(title="TID Sign Inference Backend", version="0.1.0")


def model_status() -> ModelStatus:
    settings = get_settings()
    return ModelStatus(
        word_model=settings.word_model_path.is_file(),
        sign_gate=settings.sign_gate_model_path.is_file(),
        class_names=settings.class_names_path.is_file(),
        holistic_model=settings.holistic_model_path.is_file(),
    )


@lru_cache(maxsize=1)
def get_predictor() -> TIDPredictor:
    settings = get_settings()
    return TIDPredictor(
        word_model_path=settings.word_model_path,
        sign_gate_model_path=settings.sign_gate_model_path,
        class_names_path=settings.class_names_path,
        holistic_model_path=settings.holistic_model_path,
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
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty")
    try:
        return get_predictor().predict_image_bytes(image_bytes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=f"Model asset missing: {error}") from error


@app.post("/predict/frames", response_model=FramePredictionResponse)
async def predict_frames(
    frames: Annotated[list[UploadFile], File(...)],
) -> FramePredictionResponse:
    if not frames:
        raise HTTPException(status_code=400, detail="At least one frame is required")
    try:
        frame_bytes = []
        for frame in frames:
            payload = await frame.read()
            if payload:
                frame_bytes.append(payload)
        result = get_predictor().predict_frame_bytes(frame_bytes)
        return FramePredictionResponse(
            **result.model_dump(),
            frameCount=len(frame_bytes),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=f"Model asset missing: {error}") from error
