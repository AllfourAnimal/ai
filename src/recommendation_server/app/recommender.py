from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


PreferenceMap = Dict[str, bool]
Animal = Dict[str, Optional[str]]
ANIMAL_TYPE_MAP = {"강아지": "개", "고양이": "고양이"}
SEX_CODE_MAP = {
    "수컷": {"수컷", "M"},
    "암컷": {"암컷", "F"},
    "미상": {"미상", "Q"},
}
IMAGE_FIELDS = tuple(f"popfile{i}" for i in range(1, 9))
BASE_RESPONSE_FIELDS = (
    "noticeNo",
    "colorCd",
    "careNm",
    "processState",
    "sexCd",
    "neuterYn",
)

PREFERENCE_KEYWORDS = {
    "온순함": ["얌전", "온순", "순한"],
    "호기심 많음": ["호기심"],
    "털 상태 양호": ["털 상태 양호"],
    "사람 좋아함": ["사람 좋아", "사람좋아", "사람을 좋아"],
}

ACTIVE_SCORE = {
    "상": 2,
    "중": 1,
    "하": 0,
}


def recommend_animals(
    animals: List[Animal],
    preferred_animal: Optional[str] = None,
    preferred_size: Optional[str] = None,
    preferred_species: Optional[str] = None,
    preferred_age_group: Optional[str] = None,
    sex_cd: Optional[str] = None,
    neuter_yn: Optional[str] = None,
    activity_level: Optional[str] = None,
    user_preference: Optional[PreferenceMap] = None,
) -> List[Dict[str, Any]]:
    # 1차 필터는 순서대로 한 번씩만 적용합니다.
    filtered = _filter_by_protected(animals)
    filtered = _filter_by_animal(filtered, preferred_animal)
    filtered = _filter_by_size(filtered, preferred_animal, preferred_size)
    filtered = _filter_by_species(filtered, preferred_species)
    filtered = _filter_by_age_group(filtered, preferred_age_group)
    filtered = _filter_by_sex(filtered, sex_cd)
    filtered = _filter_by_neuter(filtered, neuter_yn)

    # 2차는 남은 동물들에 점수를 부여합니다.
    scored = [
        _score_animal(animal, activity_level, user_preference or {})
        for animal in filtered
    ]
    return sorted(scored, key=lambda item: item["score"], reverse=True)


def _filter_by_animal(animals: List[Animal], preferred_animal: Optional[str]) -> List[Animal]:
    if not _has_text(preferred_animal):
        return animals
    target = _normalize_preferred_animal(preferred_animal)
    return [animal for animal in animals if _animal_type(animal) == target]


def _filter_by_protected(animals: List[Animal]) -> List[Animal]:
    return [animal for animal in animals if (animal.get("processState") or "").strip() == "보호중"]


def _filter_by_size(
    animals: List[Animal],
    preferred_animal: Optional[str],
    preferred_size: Optional[str],
) -> List[Animal]:
    if not _has_text(preferred_size) or _normalize_preferred_animal(preferred_animal) != "개":
        return animals
    return [animal for animal in animals if _match_size(animal, preferred_size)]


def _filter_by_species(animals: List[Animal], preferred_species: Optional[str]) -> List[Animal]:
    if not _has_text(preferred_species):
        return animals
    return [animal for animal in animals if _species_name(animal) == preferred_species]


def _filter_by_age_group(
    animals: List[Animal],
    preferred_age_group: Optional[str],
) -> List[Animal]:
    if not _has_text(preferred_age_group):
        return animals

    return [
        animal
        for animal in animals
        if _age_group(animal, _animal_type(animal)) == preferred_age_group
    ]


def _filter_by_sex(animals: List[Animal], sex_cd: Optional[str]) -> List[Animal]:
    if not _has_text(sex_cd):
        return animals
    target_values = _sex_values(sex_cd)
    return [animal for animal in animals if (animal.get("sexCd") or "").strip() in target_values]


def _filter_by_neuter(animals: List[Animal], neuter_yn: Optional[str]) -> List[Animal]:
    if not _has_text(neuter_yn):
        return animals
    target = neuter_yn.strip().upper()
    return [animal for animal in animals if (animal.get("neuterYn") or "").strip().upper() == target]


def _score_animal(
    animal: Animal,
    activity_level: Optional[str],
    user_preference: PreferenceMap,
) -> Dict[str, Any]:
    score = 0
    special_mark = animal.get("specialMark") or ""

    # 활동성이 높은 사용자는 "활발" 키워드가 있는 아이에게 가점을 줍니다.
    if "활발" in special_mark:
        activity_score = ACTIVE_SCORE.get(activity_level or "", 0)
        if activity_score:
            score += activity_score

    # 선호 키워드는 boolean=true 인 것만 확인합니다.
    for preference_name, enabled in user_preference.items():
        if not enabled:
            continue

        keywords = PREFERENCE_KEYWORDS.get(preference_name, [])
        if any(keyword in special_mark for keyword in keywords):
            score += 1

    result = {
        "score": score,
        "AgeGroup": _age_group(animal, _animal_type(animal)),
        "Size": _size_label(animal),
        "upKindNm": animal.get("upKindNm") or _animal_type(animal),
        "kindNm": animal.get("kindNm") or _species_name(animal),
        "specialMark": special_mark or None,
    }
    result.update({field: animal.get(field) for field in BASE_RESPONSE_FIELDS})
    result.update({field: animal.get(field) for field in IMAGE_FIELDS})
    return result


def _normalize_preferred_animal(preferred_animal: Optional[str]) -> str:
    if not _has_text(preferred_animal):
        return ""
    return ANIMAL_TYPE_MAP.get(preferred_animal.strip(), "")


def _animal_type(animal: Animal) -> str:
    up_kind_name = animal.get("upKindNm")
    if up_kind_name in {"개", "고양이"}:
        return up_kind_name

    kind_cd = animal.get("kindCd") or ""
    if "[개]" in kind_cd:
        return "개"
    if "[고양이]" in kind_cd:
        return "고양이"
    return ""


def _species_name(animal: Animal) -> Optional[str]:
    kind_name = animal.get("kindNm")
    if kind_name:
        return kind_name

    kind_cd = animal.get("kindCd") or ""
    if "]" in kind_cd:
        return kind_cd.split("]", 1)[1].strip()
    return None


def _match_size(animal: Animal, preferred_size: str) -> bool:
    weight = _parse_weight(animal.get("weight"))
    if weight is None:
        return False

    if preferred_size == "소형견":
        return weight < 8
    if preferred_size == "중형견":
        return 8 <= weight < 17
    if preferred_size == "대형견":
        return weight >= 17
    return True


def _size_label(animal: Animal) -> Optional[str]:
    if _animal_type(animal) != "개":
        return None

    weight = _parse_weight(animal.get("weight"))
    if weight is None:
        return None
    if weight < 8:
        return "소형견"
    if weight < 17:
        return "중형견"
    return "대형견"


def _parse_weight(weight_text: Optional[str]) -> Optional[float]:
    if not weight_text:
        return None

    match = re.search(r"\d+(?:\.\d+)?", weight_text)
    if not match:
        return None
    return float(match.group())


def _age_group(animal: Animal, animal_type: str) -> Optional[str]:
    age_year = _parse_birth_year(animal.get("age"))
    if age_year is None:
        return None

    current_year = datetime.now().year
    age = max(current_year - age_year, 0)

    if animal_type == "개":
        if age <= 1:
            return "어린 시기"
        if age < 7:
            return "성견·중년기"
        return "노년기"

    if animal_type == "고양이":
        if age <= 1:
            return "어린 시기"
        if age < 10:
            return "성묘·중년기"
        return "노년기"

    return None


def _parse_birth_year(age_text: Optional[str]) -> Optional[int]:
    if not age_text or len(age_text) < 4:
        return None

    year_text = age_text[:4]
    if not year_text.isdigit():
        return None
    return int(year_text)


def _sex_values(sex_cd: str) -> set[str]:
    normalized = sex_cd.strip()
    return SEX_CODE_MAP.get(normalized, {normalized})


def _has_text(value: Optional[str]) -> bool:
    return value is not None and value.strip() != ""
