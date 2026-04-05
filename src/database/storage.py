from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


Animal = Dict[str, Optional[str]]


class AnimalRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def replace_district_animals(self, district_name: str, animals: List[Animal]) -> int:
        rows = [
            (
                animal.get("desertionNo"),
                district_name,
                animal.get("processState"),
                animal.get("upKindNm"),
                animal.get("kindNm"),
                animal.get("sexCd"),
                animal.get("neuterYn"),
                animal.get("popfile1"),
                animal.get("popfile2"),
                animal.get("popfile3"),
                animal.get("popfile4"),
                animal.get("popfile5"),
                animal.get("popfile6"),
                animal.get("popfile7"),
                animal.get("popfile8"),
                json.dumps(animal, ensure_ascii=False),
                _utc_now(),
            )
            for animal in animals
            if animal.get("desertionNo")
        ]

        with sqlite3.connect(self._database_path) as connection:
            connection.execute("DELETE FROM animals WHERE district_name = ?", (district_name,))
            if rows:
                connection.executemany(
                    """
                    INSERT INTO animals (
                        desertion_no,
                        district_name,
                        process_state,
                        up_kind_nm,
                        kind_nm,
                        sex_cd,
                        neuter_yn,
                        popfile1,
                        popfile2,
                        popfile3,
                        popfile4,
                        popfile5,
                        popfile6,
                        popfile7,
                        popfile8,
                        raw_json,
                        synced_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
            connection.commit()
        return len(rows)

    def list_animals(
        self,
        *,
        process_state: Optional[str] = None,
    ) -> List[Animal]:
        query = "SELECT raw_json FROM animals"
        parameters: List[str] = []
        if process_state:
            query += " WHERE process_state = ?"
            parameters.append(process_state)
        query += " ORDER BY district_name, desertion_no"

        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [json.loads(raw_json) for (raw_json,) in rows]

    def animal_count(self) -> int:
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute("SELECT COUNT(*) FROM animals").fetchone()
        return int(row[0]) if row else 0

    def _initialize(self) -> None:
        with sqlite3.connect(self._database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS animals (
                    desertion_no TEXT PRIMARY KEY,
                    district_name TEXT NOT NULL,
                    process_state TEXT,
                    up_kind_nm TEXT,
                    kind_nm TEXT,
                    sex_cd TEXT,
                    neuter_yn TEXT,
                    popfile1 TEXT,
                    popfile2 TEXT,
                    popfile3 TEXT,
                    popfile4 TEXT,
                    popfile5 TEXT,
                    popfile6 TEXT,
                    popfile7 TEXT,
                    popfile8 TEXT,
                    raw_json TEXT NOT NULL,
                    synced_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_animals_district_name
                ON animals(district_name);

                CREATE INDEX IF NOT EXISTS idx_animals_process_state
                ON animals(process_state);
                """
            )
            self._ensure_image_columns(connection)
            connection.commit()

    def _ensure_image_columns(self, connection: sqlite3.Connection) -> None:
        existing_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(animals)").fetchall()
        }
        for column_name in (
            "popfile1",
            "popfile2",
            "popfile3",
            "popfile4",
            "popfile5",
            "popfile6",
            "popfile7",
            "popfile8",
        ):
            if column_name not in existing_columns:
                connection.execute(f"ALTER TABLE animals ADD COLUMN {column_name} TEXT")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
