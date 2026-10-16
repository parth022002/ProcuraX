# ProcuraX — Deployment and Operations Guide

**Document Reference:** Blueprint Section 22  
**Platform Version:** PoC v1.0  
**Target Environment:** Local Workstation / Production Staging / Docker Containers

---

## 1. System Requirements & Prerequisites

| Component | Minimum Version | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | 3.9.0 | 3.10+ / 3.11 | Required for backend FastAPI & ML services |
| **Node.js** | 18.0.0 | 20.x LTS | Required for React/Vite frontend |
| **npm** | 9.0.0 | 10.x | Node package manager |
| **RAM** | 4 GB | 8 GB+ | For in-memory data processing and training |
| **Disk** | 1 GB | 2 GB | Including synthetic dataset and model registries |

---

## 2. Quickstart Installation (5 Minutes)

### Step 1: Clone and Set Up Virtual Environment

```bash
# Clone the repository
git clone <repository_url> ProcuraX
cd ProcuraX

# Create and activate Python virtual environment
python -m venv venv

# Windows (Command Prompt / PowerShell):
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 2: Environment Configuration

Create a local `.env` configuration file from the template:

```bash
cp .env.example .env
```

*Note: ProcuraX runs 100% locally out-of-the-box. Live external signal API keys (Marketaux, Alpha Vantage, NewsData.io) are optional; GDELT operates without authentication, and all adapters automatically fall back to deterministic high-fidelity fixtures if keys are omitted.*

### Step 3: Frontend Installation

```bash
cd frontend
npm install
cd ..
```

---

## 3. Data Generation & Model Registry Setup

Initialize the reproducible synthetic data foundation and train the baseline model:

```bash
# 1. Generate the 8 synthetic relational tables (seed=42)
python scripts/generate_synthetic_data.py --scale small

# 2. Run data quality and leakage checks
python scripts/data_quality_validator.py

# 3. Train and register the baseline Logistic Regression model
python -m backend.app.services.risk_model.train
```

*Verification:* Confirm that `data/generated/` contains 8 CSV files and `models/registry/` contains `logistic_model.pkl` and `logistic_model_card.json`.

---

## 4. Running the Application

### Option A: Running Development Servers

Open two terminal sessions:

**Terminal 1 — Backend API (FastAPI):**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*API Swagger Documentation:* `http://localhost:8000/docs`  
*Health Check:* `http://localhost:8000/api/v1/health`

**Terminal 2 — Frontend Application (Vite / React):**
```bash
cd frontend
npm run dev
```
*Web Application:* `http://localhost:5173`

---

### Option B: Building for Production

To create a static production build of the frontend:

```bash
cd frontend
npm run build
```
The compiled assets will be placed in `frontend/dist/`. These static assets can be served via Nginx, Caddy, or mounted directly by FastAPI.

---

## 5. Automated Verification & Replay Runbook

ProcuraX includes three automated verification and showcase scripts:

### 1. 5-Minute Decision Loop Showcase Replay
Executes all 8 operational stages against the active backend without needing browser interaction:
```bash
python scripts/run_decision_loop_replay.py
```

### 2. Comprehensive Test Suite
Executes the full unit, integration, state machine, and governance test suite:
```bash
python -m pytest backend/tests -v
```

### 3. Master Full Regression Quality Gate
Executes repo verification, bytecode compilation, data validation, pytest, secret scanning, replay pipeline, and frontend production build:
```bash
python scripts/full_regression_check.py
```

---

## 6. API Health & Diagnostic Endpoints

| Endpoint | Method | Expected Status | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/health` | GET | `200 OK` | Gateway operational status and active version. |
| `/api/v1/signals/providers` | GET | `200 OK` | Health and connectivity status for all 5 external signal adapters. |
| `/api/v1/risk/model-card` | GET | `200 OK` | Current model card, ROC-AUC, Brier score, and held-out contamination guard. |
| `/api/v1/cases` | GET | `200 OK` | Active disruption cases and state machine history. |
| `/api/v1/copilot/documents` | GET | `200 OK` | List of authorized governance contracts and policy documents. |

---

## 7. Troubleshooting & Operational FAQs

**Q: Why do I see a warning about unconfigured signal adapters?**  
*A:* This is standard behavior. Only GDELT requires no API key. Other providers (Marketaux, NewsData.io) display `not_configured` unless API keys are placed in `.env`. The system automatically falls back to deterministic cached fixtures.

**Q: How do I verify that `SUP-1047` does not leak into model training?**  
*A:* Run `python -m pytest backend/tests/test_risk_model.py -k test_no_leakage_apex_flagship`. The test strictly asserts that `SUP-1047` rows during the disruption window (`2026-07-02` to `2026-09-30`) never enter the training set.

**Q: Can the platform automatically create purchase orders in SAP or Oracle?**  
*A:* No. By architectural design, all generated action packets are proposal-only (`is_proposal_only: True`). Live automated write-back is prohibited to ensure enterprise safety.
