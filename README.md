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

[![EcoNav CI/CD](https://github.com/hitendras510/EcoNav-AI/actions/workflows/main.yml/badge.svg)](https://github.com/hitendras510/EcoNav-AI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-Compliant-10b981)](https://github.com/OpenEnv/spec)

EcoNav AI is an **intelligent routing platform** and Reinforcement Learning (RL) environment built for the **Meta AI Environmental Decision Intelligence Hackathon**. It empowers users and agents to navigate urban networks while minimizing pollution exposure and maximizing health "Exposure Credits."

---

## 🌍 Project Overview

EcoNav AI transforms navigation from a simple distance-minimization problem into a **multi-objective environmental optimization task**. By integrating real-time Air Quality Index (AQI) data with dynamic traffic simulations, the platform provides a realistic testing ground for eco-aware agents.

### Key Innovations:
- **Live AQI Integration**: Real-time pollution data fetched from the Open-Meteo API for 50+ network nodes across India.
- **Exposure Credits**: A gamified health currency that penalizes high-pollution segments (Grade F) and rewards clean-air segments (Grade A).
- **Dynamic Traffic Engine**: Simulates congestion levels that impact both travel time and localized pollution exposure.
- **OpenEnv Compliance**: Fully compatible with the OpenEnv specification for RL evaluation and agent deployment.

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
EcoNav-AI/
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
   git clone https://github.com/hitendras510/EcoNav-AI.git
   cd EcoNav-AI
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
| **Real-time Data** | Active (Open-Meteo) 🛰️ |
| **Model Version** | EcoScorer v2.1 🧠 |

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.
