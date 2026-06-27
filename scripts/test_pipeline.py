"""Smoke-test the core EcoNav workflow."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.backend.services.route_service import get_route_service
from models.train_model import run_training_pipeline


def run_smoke_tests() -> None:
    assert run_training_pipeline(), "Training pipeline failed"

    response = get_route_service("A", "F")
    assert "route" in response and response["route"], "Route generation failed"
    assert response["route"][0] == "A", "Route should start at source"
    assert response["route"][-1] == "F", "Route should end at destination"

    invalid = get_route_service("X", "F")
    assert invalid.get("error") == "Invalid start or end node", "Validation behavior changed"


if __name__ == "__main__":
    run_smoke_tests()
    print("All smoke tests passed ✅")
