from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = ROOT_DIR / ".env"
DEFAULT_DISTRICT_REGISTRY_PATH = ROOT_DIR / "src" / "database" / "config" / "seoul_districts.json"


@dataclass(frozen=True)
class DatabaseSettings:
    service_key: str
    district_registry_path: Path
    timeout_seconds: float = 20.0


def load_settings(env_path: Optional[Path] = None) -> DatabaseSettings:
    dotenv_path = env_path or DEFAULT_ENV_PATH
    _load_dotenv(dotenv_path)

    service_key = os.getenv("ANIMAL_API_SERVICE_KEY", "").strip()
    if not service_key:
        raise RuntimeError(
            "ANIMAL_API_SERVICE_KEY is not set. Add it to the repository root .env file."
        )

    district_registry_path = Path(
        os.getenv("ANIMAL_DISTRICT_REGISTRY_PATH", str(DEFAULT_DISTRICT_REGISTRY_PATH))
    ).expanduser()
    timeout_seconds = float(os.getenv("ANIMAL_API_TIMEOUT_SECONDS", "20"))

    return DatabaseSettings(
        service_key=service_key,
        district_registry_path=district_registry_path,
        timeout_seconds=timeout_seconds,
    )


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)
