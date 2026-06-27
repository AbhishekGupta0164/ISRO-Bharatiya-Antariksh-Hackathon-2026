import json
from pathlib import Path

from models.train_model import run_training_pipeline

MODEL_PATH = Path("models/eco_model.json")


def test_training_pipeline_writes_json_model():
    assert run_training_pipeline()
    assert MODEL_PATH.exists()

    payload = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    assert set(payload.keys()) == {"distance_weight", "pollution_weight", "exposure_weight"}
