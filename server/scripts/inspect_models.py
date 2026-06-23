from __future__ import annotations

import json

from app.config import get_settings
from app.model_registry import inspect_model_files


def main() -> None:
    settings = get_settings()
    result = inspect_model_files(
        word_model_path=settings.word_model_path,
        sign_gate_model_path=settings.sign_gate_model_path,
        class_names_path=settings.class_names_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
