"""Create deterministic demo data files used by simulator/training."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


ROUTE_ROWS = [
    {"distance": 5, "traffic": 8, "fuel": 5.1},
    {"distance": 4, "traffic": 3, "fuel": 2.6},
    {"distance": 7, "traffic": 6, "fuel": 5.2},
    {"distance": 2, "traffic": 1, "fuel": 1.0},
    {"distance": 9, "traffic": 9, "fuel": 7.1},
]

AQI_ROWS = [
    {"city": "A", "aqi": 75},
    {"city": "B", "aqi": 120},
    {"city": "C", "aqi": 48},
    {"city": "D", "aqi": 62},
    {"city": "E", "aqi": 35},
    {"city": "F", "aqi": 41},
]


def _write_csv(path: Path, rows: list[dict[str, int | float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def seed() -> None:
    _write_csv(DATA_DIR / "routes.csv", ROUTE_ROWS)
    _write_csv(DATA_DIR / "raw" / "aqi_data.csv", AQI_ROWS)


if __name__ == "__main__":
    seed()
    print("Seed data generated in data/routes.csv and data/raw/aqi_data.csv")
