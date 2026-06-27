---
title: EcoNav AI
emoji: 🌍
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: true
---

# 🌱 EcoNav AI — Exposure Credit Platform

[![EcoNav CI/CD](https://github.com/AbhishekGupta0164/ISRO---Bharatiya-Antariksh-Hackathon-2026/actions/workflows/main.yml/badge.svg)](https://github.com/AbhishekGupta0164/ISRO---Bharatiya-Antariksh-Hackathon-2026/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-Compliant-10b981)](https://github.com/OpenEnv/spec)

EcoNav AI is an **advanced satellite-driven environmental intelligence platform** built for the **ISRO Bharatiya Antariksh Hackathon 2026 (PS-3)**. It aggregates multi-sensor satellite products to predict ground-level PM2.5, clusters formaldehyde (HCHO) hotspots to trace agricultural burning, validates predictions against CPCB monitors, and offers a downstream multi-objective routing app that minimizes pollution exposure.

---

## 🌍 Project Overview

EcoNav AI transforms environmental decision intelligence from a weather forecast blend into a **satellite-observed, validated spatial forecasting system**. By integrating satellite columns, meteorological parameters, and ground observations, the platform estimates real-time PM2.5 at 0.1° (~10km) resolution across India.

### Key Innovations:
- **INSAT-3D AOD Pipeline**: Real-time FTP downloading and h5py processing of Aerosol Optical Depth from MOSDAC.
- **Copernicus TROPOMI Gridder**: Automates querying Sentinel-5P catalogs (HCHO, NO2, SO2, CO) and gridding column densities to a 0.1° bbox grid.
- **CNN-LSTM Temporal Predictor**: A deep learning architecture mapping 14-day history of AOD + tropospheric gases + meteorology to surface PM2.5.
- **HCHO Hotspot Clustered Avoidance**: DBSCAN spatial clustering identifies seasonal agricultural (e.g., Punjab stubble) and forest fires (e.g., Odisha), generating polygons bypassed by routing.
- **NASA FIRMS Fire Correlation**: Links active fires within 50km to HCHO anomalies with lag cross-correlation checks.
- **CPCB Validation Engine**: Ground truth verification reporting RMSE, MAE, and R² scores utilizing OpenAQ API v3.

---

## 🛠 Tech Stack

The project is architected as a modern **monorepo** for seamless development and deployment.

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic, Torch (ML scoring).
- **Frontend**: Vite, Vanilla JS, CSS3 (Glassmorphism), Leaflet.js (Mapping), Chart.js (Analytics).
- **Infrastructure**: Docker, Turbo (Build system), GitHub Actions (CI/CD).
- **Quality**: Ruff (Linting), Prettier (Formatting).

---

## 📂 Repository Structure

```text
ISRO---Bharatiya-Antariksh-Hackathon-2026/
├── apps/
│   ├── backend/         # FastAPI server, AI services, and RL endpoints
│   ├── frontend/        # Vite-powered dashboard and mapping interface
│   ├── simulator/       # ML training and evaluation logic
├── packages/
│   ├── env_core/        # Shared RL environment logic (OpenEnv Spec)
│   ├── exposure-engine/ # Pollution exposure calculation primitives
│   └── agent-engine/    # Baseline agent policies and LLM integration
├── requirements/        # Modularized dependency lists
├── server/              # Production entry points for Docker/HF Spaces
├── turbo.json           # Monorepo configuration
└── inference.py         # Baseline agent evaluation script (Compliance optimized)
```

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: >= 18.0.0
- **Python**: >= 3.10
- **npm**: >= 11.11.0
- **Docker**: (Optional) For containerized deployment

### Quick Start (Recommended)
1. **Clone the repository**:
   ```bash
   git clone https://github.com/AbhishekGupta0164/ISRO---Bharatiya-Antariksh-Hackathon-2026.git
   cd ISRO---Bharatiya-Antariksh-Hackathon-2026
   ```

2. **Install Dependencies**:
   ```bash
   npm install                               # Installs monorepo build tools
   pip install -r requirements/backend.txt   # Installs Python backend deps
   ```

3. **Run Dev Environment**:
   Use the Turbo-powered development command to start both the backend and frontend:
   ```bash
   npm run dev
   ```

### Manual Startup
- **Backend**: `python server/app.py` (Runs on [http://localhost:7860](http://localhost:7860))
- **Frontend**: `npm run dev --prefix apps/frontend` (Runs on [http://localhost:5173](http://localhost:5173))

---

## 🐋 Docker Deployment

EcoNav AI is fully containerized and ready for deployment on Hugging Face Spaces or your local infrastructure.

### 1. Build & Run (Single Container)
This builds both the frontend and backend into a single production-ready image.

```bash
# Build the image
docker build -t econav-ai .

# Run the container
docker run -p 7860:7860 econav-ai
```
The application will be available at [http://localhost:7860](http://localhost:7860).

### 2. Using Docker Compose
For development with separate services:

```bash
docker-compose -f infra/docker/docker-compose.yml up --build
```

---

## 🧠 RL Evaluation (OpenEnv Compliance)

The environment supports four standard evaluation tasks of increasing complexity:
1. `easy_route`: Delhi to Kolkata (15 steps).
2. `medium_route`: Delhi to Kolkata (8 steps).
3. `hard_pollution_dodge`: Agra to Kolkata (6 steps).
4. `expert_credit_max`: Maximize credits while reaching the goal (10 steps).

**Running Baseline Evaluation**:
The `inference.py` script is optimized for OpenEnv compliance, featuring structured logging (`[START]`, `[STEP]`, `[END]`) and LLM agent support.

```bash
export ENV_URL="http://localhost:7860"
export HF_TOKEN="your_huggingface_token"
python inference.py
```

---

## 🧪 Development & Quality

We maintain high code quality standards through automated linting and formatting.

- **Linting (Python)**: `ruff check .`
- **Fix Linting**: `ruff check --fix .`
- **Formatting (JS/TS/MD)**: `npm run format`

---

## 🏆 Project Status

| Check | Status |
|---|---|
| **CI/CD Pipeline** | Passing ✅ |
| **OpenEnv Spec** | Compliant (v1.0) 🟢 |
| **Real-time Data** | Active (MOSDAC INSAT-3D + Copernicus TROPOMI) 🛰️ |
| **Model Version** | SatAQI CNN-LSTM v1.0 🧠 |

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.
