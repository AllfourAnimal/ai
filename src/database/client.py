from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.parse import unquote, urlencode
from urllib.request import Request, urlopen

from .config import DatabaseSettings
from .models import ANIMAL_ITEM_FIELDS, ShelterRecord


SHELTER_API_URL = "http://apis.data.go.kr/1543061/abandonmentPublicService_v2/shelter_v2"
ABANDONMENT_API_URL = "http://apis.data.go.kr/1543061/abandonmentPublicService_v2/abandonmentPublic_v2"


class GovAnimalApiClient:
    def __init__(self, settings: DatabaseSettings) -> None:
        self._service_key = _normalize_service_key(settings.service_key)
        self._timeout_seconds = settings.timeout_seconds

    def fetch_shelters(self, upr_cd: str, org_cd: str) -> list[ShelterRecord]:
        payload = self._request_json(
            SHELTER_API_URL,
            {
                "upr_cd": upr_cd,
                "org_cd": org_cd,
                "_type": "json",
            },
        )
        items = _extract_items(payload)
        return [_to_shelter_record(item) for item in items]

    def fetch_abandoned_animals(
        self,
        care_reg_no: str,
        *,
        page_no: int = 1,
        num_of_rows: int = 100,
    ) -> tuple[list[Dict[str, Optional[str]]], int]:
        payload = self._request_json(
            ABANDONMENT_API_URL,
            {
                "care_reg_no": care_reg_no,
                "pageNo": page_no,
                "numOfRows": num_of_rows,
                "_type": "json",
            },
        )
        items = _extract_items(payload)
        total_count = _extract_total_count(payload)
        return ([_to_animal_record(item) for item in items], total_count)

    def _request_json(self, base_url: str, params: dict[str, Any]) -> dict[str, Any]:
        encoded_params = urlencode(
            {
                "serviceKey": self._service_key,
                **params,
            }
        )
        request = Request(
            url=f"{base_url}?{encoded_params}",
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urlopen(request, timeout=self._timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


def _normalize_service_key(value: str) -> str:
    return unquote(value.strip())


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    body = _extract_body(payload)
    items = body.get("items", {}).get("item", [])
    if isinstance(items, list):
        return items
    if isinstance(items, dict):
        return [items]
    return []


def _extract_total_count(payload: dict[str, Any]) -> int:
    raw_total_count = _extract_body(payload).get("totalCount", 0)
    try:
        return int(raw_total_count)
    except (TypeError, ValueError):
        return 0


def _extract_body(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("body"), dict):
        return payload["body"]
    return payload.get("response", {}).get("body", {})


def _to_shelter_record(item: dict[str, Any]) -> ShelterRecord:
    return ShelterRecord(
        care_reg_no=str(item.get("careRegNo", "")),
        care_name=str(item.get("careNm", "")),
        care_addr=str(item.get("careAddr", "")),
        care_tel=str(item.get("careTel", "")),
        upr_cd=str(item.get("uprCd", "")),
        org_cd=str(item.get("orgCd", "")),
        lat=str(item.get("lat", "")),
        lng=str(item.get("lng", "")),
        save_target_animal=str(item.get("saveTrgtAnimal", "")),
        raw=item,
    )


def _to_animal_record(item: dict[str, Any]) -> Dict[str, Optional[str]]:
    return _normalize_animal_item(item)


def _normalize_animal_item(item: dict[str, Any]) -> Dict[str, Optional[str]]:
    normalized: Dict[str, Optional[str]] = {}
    for key in ANIMAL_ITEM_FIELDS:
        normalized[key] = _optional_string(item.get(key))
    return normalized


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    if text == "":
        return None
    return text
