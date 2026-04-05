from __future__ import annotations

import json
from dataclasses import asdict

from .client import GovAnimalApiClient
from .config import load_settings
from .registry import DistrictRegistry
from .service import SeoulAnimalSyncService
from .storage import AnimalRepository


def main() -> None:
    settings = load_settings()
    repository = AnimalRepository(settings.database_path)
    registry = DistrictRegistry.from_json(settings.district_registry_path)
    service = SeoulAnimalSyncService(
        GovAnimalApiClient(settings),
        registry,
        repository,
    )
    summaries = [asdict(summary) for summary in service.sync_all_seoul()]
    print(json.dumps({"databasePath": str(settings.database_path), "summaries": summaries}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
