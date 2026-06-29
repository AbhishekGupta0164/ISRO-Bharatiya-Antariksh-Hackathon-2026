import json
import os
from statistics import mean

MODEL_PATH = "models/eco_model.json"


def run_training_pipeline(epochs: int = 1) -> bool:
    _ = epochs
    samples = [
        {"distance": 5.0, "pollution": 10.0, "exposure": 50.0, "score": 9.5},
        {"distance": 8.0, "pollution": 3.0, "exposure": 24.0, "score": 4.5},
        {"distance": 4.0, "pollution": 2.0, "exposure": 8.0, "score": 2.4},
    ]

    distance_weight = mean(s["score"] / max(s["distance"], 1.0) for s in samples) * 0.2
    pollution_weight = mean(s["score"] / max(s["pollution"], 1.0) for s in samples) * 0.3
    exposure_weight = mean(s["score"] / max(s["exposure"], 1.0) for s in samples) * 0.5

    model = {
        "distance_weight": round(distance_weight, 4),
        "pollution_weight": round(pollution_weight, 4),
        "exposure_weight": round(exposure_weight, 4),
    }

    os.makedirs("models", exist_ok=True)
    with open(MODEL_PATH, "w", encoding="utf-8") as fp:
        json.dump(model, fp, indent=2)

    print(f"Model trained and saved to {MODEL_PATH}")
    return True


if __name__ == "__main__":
    run_training_pipeline()
