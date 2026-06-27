#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements/backend.txt
python -m pip install -r requirements/frontend.txt
python -m pip install -r requirements/ml.txt
python -m pip install pytest ruff

echo "✅ EcoNav dependencies installed"
