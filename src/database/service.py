from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .client import GovAnimalApiClient
from .models import DistrictCode, ShelterRecord
from .registry import DistrictRegistry
from .storage import AnimalRepository


Animal = Dict[str, Optional[str]]


@dataclass(frozen=True)
class SyncSummary:
    district_name: str
    shelter_count: int
    animal_count: int


class SeoulAnimalSyncService:
    def __init__(
        self,
        client: GovAnimalApiClient,
        registry: DistrictRegistry,
        repository: AnimalRepository,
    ) -> None:
        self._client = client
        self._registry = registry
        self._repository = repository

    def sync_all_seoul(self) -> List[SyncSummary]:
        return [self.sync_district(district) for district in self._registry.seoul_districts()]

    def sync_district(self, district: DistrictCode) -> SyncSummary:
        shelters = sorted(
            self._client.fetch_shelters(district.upr_cd, district.org_cd),
            key=lambda shelter: shelter.care_name,
        )

        animals = self._collect_animals(shelters)
        stored_count = self._repository.replace_district_animals(district.name, animals)
        return SyncSummary(
            district_name=district.name,
            shelter_count=len(shelters),
            animal_count=stored_count,
        )

    def _collect_animals(self, shelters: List[ShelterRecord]) -> List[Animal]:
        animals_by_id: Dict[str, Animal] = {}

        for shelter in shelters:
            if not shelter.care_reg_no:
                continue

            page_no = 1
            fetched_for_shelter = 0
            while True:
                animals, total_count = self._client.fetch_abandoned_animals(
                    shelter.care_reg_no,
                    page_no=page_no,
                    num_of_rows=100,
                )
                if not animals:
                    break

                fetched_for_shelter += len(animals)
                for animal in animals:
                    desertion_no = animal.get("desertionNo")
                    if desertion_no:
                        animals_by_id[desertion_no] = animal

                if fetched_for_shelter >= total_count:
                    break
                page_no += 1

        return list(animals_by_id.values())
