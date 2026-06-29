#!/usr/bin/env bash
set -euo pipefail

python scripts/seed_data.py
python models/train_model.py
python scripts/test_pipeline.py

uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

streamlit run apps/frontend/app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup EXIT
wait
