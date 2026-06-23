from __future__ import annotations

from app.main import model_status


def main() -> None:
    print(model_status().model_dump_json(indent=2))


if __name__ == "__main__":
    main()
