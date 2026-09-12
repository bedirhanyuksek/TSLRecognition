from __future__ import annotations

import hashlib
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path


# Official MediaPipe Holistic Landmarker model bundle.
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/"
    "holistic_landmarker/float16/latest/holistic_landmarker.task"
)
EXPECTED_SHA256 = "e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8"
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "holistic_landmarker.task"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    if MODEL_PATH.exists():
        actual = sha256(MODEL_PATH)
        if actual == EXPECTED_SHA256:
            print(f"MediaPipe model already verified: {MODEL_PATH}")
            return 0
        print(
            f"Existing model has an unexpected SHA-256: {MODEL_PATH}",
            file=sys.stderr,
        )
        return 1

    temporary_path = MODEL_PATH.with_suffix(".task.download")
    try:
        request = urllib.request.Request(
            MODEL_URL,
            headers={"User-Agent": "TSLRecognition-model-setup"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            with temporary_path.open("wb") as output:
                shutil.copyfileobj(response, output)

        actual = sha256(temporary_path)
        if actual != EXPECTED_SHA256:
            print(
                "Downloaded MediaPipe model failed SHA-256 verification.",
                file=sys.stderr,
            )
            return 1

        temporary_path.replace(MODEL_PATH)
        print(f"MediaPipe model downloaded and verified: {MODEL_PATH}")
        return 0
    except (OSError, urllib.error.URLError) as error:
        print(f"Failed to download MediaPipe model: {error}", file=sys.stderr)
        return 1
    finally:
        temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
