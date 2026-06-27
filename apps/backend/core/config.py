from __future__ import annotations

import os


class Settings:
    APP_NAME = "EcoNav AI API"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    MODEL_PATH = os.getenv("MODEL_PATH", "models/eco_model.json")
    TRAINING_INTERVAL_SECONDS = int(os.getenv("TRAINING_INTERVAL_SECONDS", "600"))


settings = Settings()
