from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "routes.csv"
MODEL_PATH = ROOT / "models" / "fuel_model.pkl"


def train_fuel_model() -> Path:
    data = pd.read_csv(DATA_PATH).dropna()
    x_train = data[["distance", "traffic"]]
    y_train = data["fuel"]

    model = LinearRegression()
    model.fit(x_train, y_train)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return MODEL_PATH


if __name__ == "__main__":
    path = train_fuel_model()
    print(f"✅ Model trained successfully at {path}")
