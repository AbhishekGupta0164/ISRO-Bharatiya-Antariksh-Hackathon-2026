# 🤝 Contributing to VayuNetra

Welcome to the team! This guide explains how to fork, work on, and contribute code to this project so every team member stays in sync and the app auto-deploys on every merge.

---

## 📐 How the Workflow Works

```
Your Fork ──► PR to main repo ──► Review & Merge ──► Auto Deploy to Vercel 🚀
```

| Branch / Event | What Happens |
|---|---|
| Push to **any branch** (your fork) | Tests + lint run on CI |
| Open a **Pull Request** to `main` | Tests run + Vercel **Preview URL** generated |
| **Merge to `main`** | Tests run → Docker build → **Deploy to Vercel (Production)** |

---

## 🚀 First-Time Setup (Do this once)

### Step 1 — Fork the repo
Go to: `https://github.com/AbhishekGupta0164/ISRO---Bharatiya-Antariksh-Hackathon-2026`

Click **Fork** → it creates `YOUR_USERNAME/ISRO---Bharatiya-Antariksh-Hackathon-2026` under your account.

---

### Step 2 — Clone your fork locally
```bash
git clone https://github.com/YOUR_USERNAME/ISRO---Bharatiya-Antariksh-Hackathon-2026.git
cd ISRO---Bharatiya-Antariksh-Hackathon-2026
```

---

### Step 3 — Add upstream (main repo) as a remote
This lets you pull the latest changes from the main repo anytime.
```bash
git remote add upstream https://github.com/AbhishekGupta0164/ISRO---Bharatiya-Antariksh-Hackathon-2026.git
```

Verify remotes:
```bash
git remote -v
# origin    https://github.com/YOUR_USERNAME/ISRO---Bharatiya-Antariksh-Hackathon-2026.git (fetch)
# upstream  https://github.com/AbhishekGupta0164/ISRO---Bharatiya-Antariksh-Hackathon-2026.git (fetch)
```

---

### Step 4 — Install dependencies
```bash
# Python backend
pip install -r requirements/backend.txt -r requirements/ml.txt

# Node / Frontend
npm install
```

---

## 🔄 Daily Workflow

### Before starting any work — sync with upstream
Always pull the latest code from the main repo before making changes:
```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main   # update your fork too
```

---

### Create a feature branch
**Never commit directly to `main`.** Always work on a branch:
```bash
git checkout -b feature/your-feature-name
# examples:
# git checkout -b feature/add-route-api
# git checkout -b fix/aqi-fetch-bug
# git checkout -b docs/update-readme
```

---

### Make your changes, then commit
```bash
git add .
git commit -m "feat: describe what you did"
```

Use clear commit messages:
| Prefix | Use for |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `chore:` | Config/tooling changes |
| `test:` | Adding or fixing tests |

---

### Push to your fork
```bash
git push origin feature/your-feature-name
```

---

### Open a Pull Request
1. Go to your fork on GitHub
2. Click **"Compare & pull request"**
3. Set base repo: `AbhishekGupta0164/ISRO---Bharatiya-Antariksh-Hackathon-2026` → base branch: `main`
4. Write a clear title and description
5. Submit the PR

> 🔍 A **Vercel Preview URL** will automatically be generated for your PR so the team can review the live changes before merging.

---

### After your PR is merged
Once merged to `main`, the production Vercel deployment will **automatically update** within ~2 minutes.

Sync your local `main` again:
```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

---

## 🏗 Project Structure (Quick Reference)

```
├── apps/
│   ├── backend/         ← FastAPI server (Python)
│   ├── frontend/        ← Vite + Vanilla JS dashboard
│   └── simulator/       ← ML training & evaluation
├── packages/
│   ├── env_core/        ← RL environment logic
│   ├── exposure-engine/ ← Pollution scoring engine
│   └── agent-engine/    ← RL agent policies
├── data/                ← CSVs, AQI data
├── models/              ← ML model files
├── requirements/        ← Python deps (backend/ml/frontend)
├── scripts/             ← Data seeding, pipeline tests
├── tests/               ← Test files
├── vercel.json          ← Vercel deployment config
└── .github/workflows/   ← CI/CD pipelines
```

---

## 🧪 Running Locally

```bash
# Backend (runs on http://localhost:7860)
python server/app.py

# Frontend (runs on http://localhost:5173)
npm run dev --prefix apps/frontend

# Or run both together
npm run dev
```

---

## 🔐 Secrets (Only repo owner needs to set these)

Go to: **Repo → Settings → Secrets and variables → Actions**

| Secret | Where to get it |
|---|---|
| `VERCEL_TOKEN` | vercel.com → Settings → Tokens |
| `VERCEL_ORG_ID` | vercel.com → Settings → General → Team ID |
| `VERCEL_PROJECT_ID` | Your Vercel project → Settings → General |

---

## ❓ Rules

- ✅ Always branch from `main`
- ✅ Always sync upstream before starting work
- ✅ Always open a PR — never push directly to `main`
- ✅ Wait for CI to pass before asking for a review
- ❌ Do not push secrets or API keys to the repo
