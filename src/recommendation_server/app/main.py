from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .recommender import recommend_animals


ROOT_DIR = Path(__file__).resolve().parents[3]
DB_PATH = ROOT_DIR / "data" / "seoul_animals.db"
STATIC_DIR = Path(__file__).resolve().parent / "static"
PROTECTED_ANIMALS_QUERY = """
SELECT raw_json
FROM animals
WHERE process_state = ?
ORDER BY district_name, desertion_no
"""

app = FastAPI(title="Recommendation Server")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class RecommendationRequest(BaseModel):
    preferredAnimal: Optional[str] = None
    preferredSize: Optional[str] = None
    preferredSpecies: Optional[str] = None
    preferredAgeGroup: Optional[str] = None
    sexCd: Optional[str] = None
    neuterYn: Optional[str] = None
    activityLevel: Optional[str] = None
    userPreference: Dict[str, bool] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    count: int
    recommendations: List[Dict[str, Any]]


@app.get("/")
def prototype() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    animals = _load_animals()
    recommendations = recommend_animals(
        animals=animals,
        preferred_animal=request.preferredAnimal,
        preferred_size=request.preferredSize,
        preferred_species=request.preferredSpecies,
        preferred_age_group=request.preferredAgeGroup,
        sex_cd=request.sexCd,
        neuter_yn=request.neuterYn,
        activity_level=request.activityLevel,
        user_preference=request.userPreference,
    )
    return RecommendationResponse(count=len(recommendations), recommendations=recommendations)


def _load_animals() -> List[Dict[str, Optional[str]]]:
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(PROTECTED_ANIMALS_QUERY, ("보호중",)).fetchall()

    if not rows:
        raise HTTPException(status_code=500, detail="No protected animals found in database.")
    return [json.loads(raw_json) for (raw_json,) in rows]
