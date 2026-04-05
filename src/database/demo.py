from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .client import GovAnimalApiClient
from .config import ROOT_DIR, load_settings
from .registry import DistrictRegistry
from .service import AnimalAbandonmentService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch shelters and abandoned animals for selected Seoul districts."
    )
    parser.add_argument(
        "--district",
        action="append",
        dest="districts",
        default=None,
        help="District name from the registry. Repeat this option to add more districts.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of animal records to collect per district.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional path to a .env file.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional output JSON file path. Defaults to the repository output directory.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = load_settings(args.env_file)
    registry = DistrictRegistry.from_json(settings.district_registry_path)
    client = GovAnimalApiClient(settings)
    service = AnimalAbandonmentService(client, registry)

    requested_districts = args.districts or ["동대문구", "강남구"]
    unique_districts = list(dict.fromkeys(requested_districts))
    results = [
        asdict(service.fetch_district_animals(district_name, args.limit))
        for district_name in unique_districts
    ]
    output_file = args.output_file or _default_output_file()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved results to {output_file}")


def _default_output_file() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return ROOT_DIR / "output" / f"animal_demo_{timestamp}.json"


if __name__ == "__main__":
    main()
