from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .client import GovAnimalApiClient
from .models import AnimalRecord, ShelterRecord, ShelterSummary
from .registry import DistrictRegistry


@dataclass(frozen=True)
class DistrictAnimalsResult:
    district_name: str
    district_org_cd: str
    district_upr_cd: str
    requested_animals: int
    shelter_count: int
    collected_animals: int
    shelters: list[ShelterSummary]
    animals: list[Dict[str, Optional[str]]]


class AnimalAbandonmentService:
    def __init__(
        self,
        client: GovAnimalApiClient,
        registry: DistrictRegistry,
    ) -> None:
        self._client = client
        self._registry = registry

    def fetch_district_animals(
        self,
        district_name: str,
        animal_limit: int = 100,
    ) -> DistrictAnimalsResult:
        district = self._registry.get_by_name(district_name)
        shelters = sorted(
            self._client.fetch_shelters(district.upr_cd, district.org_cd),
            key=lambda shelter: shelter.care_name,
        )
        animals = self._collect_animals(shelters, animal_limit)
        return DistrictAnimalsResult(
            district_name=district.name,
            district_org_cd=district.org_cd,
            district_upr_cd=district.upr_cd,
            requested_animals=animal_limit,
            shelter_count=len(shelters),
            collected_animals=len(animals),
            shelters=[_to_shelter_summary(shelter) for shelter in shelters],
            animals=animals,
        )

    def _collect_animals(
        self,
        shelters: list[ShelterRecord],
        animal_limit: int,
    ) -> list[Dict[str, Optional[str]]]:
        collected: list[Dict[str, Optional[str]]] = []
        page_size = 100

        for shelter in shelters:
            if len(collected) >= animal_limit or not shelter.care_reg_no:
                break

            page_no = 1
            fetched_for_shelter = 0
            while len(collected) < animal_limit:
                animals, total_count = self._client.fetch_abandoned_animals(
                    shelter.care_reg_no,
                    page_no=page_no,
                    num_of_rows=page_size,
                )

                if not animals:
                    break

                fetched_for_shelter += len(animals)
                protected_animals = [
                    _to_animal_summary(animal)
                    for animal in animals
                    if _is_protected(animal)
                ]
                remaining = animal_limit - len(collected)
                collected.extend(protected_animals[:remaining])

                if len(collected) >= animal_limit or fetched_for_shelter >= total_count:
                    break

                page_no += 1

        return collected


def _to_shelter_summary(shelter: ShelterRecord) -> ShelterSummary:
    return ShelterSummary(
        care_reg_no=shelter.care_reg_no,
        care_name=shelter.care_name,
        care_addr=shelter.care_addr,
        care_tel=shelter.care_tel,
        lat=shelter.lat,
        lng=shelter.lng,
        save_target_animal=shelter.save_target_animal,
    )


def _is_protected(animal: AnimalRecord) -> bool:
    process_state = animal.fields.get("processState")
    return process_state is not None and process_state.strip() == "보호중"


def _to_animal_summary(animal: AnimalRecord) -> Dict[str, Optional[str]]:
    return dict(animal.fields)
