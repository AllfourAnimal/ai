from __future__ import annotations

import json
from pathlib import Path

from .models import DistrictCode


class DistrictRegistry:
    def __init__(self, districts: list[DistrictCode]) -> None:
        self._districts = districts
        self._by_name = {district.name: district for district in districts}

    @classmethod
    def from_json(cls, path: Path) -> "DistrictRegistry":
        payload = json.loads(path.read_text(encoding="utf-8"))
        districts = [
            DistrictCode(
                upr_cd=str(item["upr_cd"]),
                org_cd=str(item["org_cd"]),
                name=str(item["name"]),
            )
            for item in payload
        ]
        return cls(districts)

    def all(self) -> list[DistrictCode]:
        return list(self._districts)

    def get_by_name(self, name: str) -> DistrictCode:
        normalized_name = name.strip()
        try:
            return self._by_name[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Unknown district name: {name}") from exc
