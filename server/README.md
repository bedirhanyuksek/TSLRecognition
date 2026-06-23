# TID Sign Inference Backend

FastAPI backend for the React Native TID translator prototype.

## Run

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /health` returns backend and model readiness.
- `POST /predict/image` accepts one image and returns a prediction-shaped response.

Model weights live under `server/models/` and are intentionally ignored by git.
