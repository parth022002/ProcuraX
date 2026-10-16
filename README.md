# ProcuraX — Sovereign Decision Intelligence for Supply Chain Disruption

<div align="center">
  <img src="frontend/public/procurax-neon-emblem.webp" alt="ProcuraX Logo" width="160" />
  <p><strong>Predict. Quantify. Simulate. Ground. Govern.</strong></p>
  <p><em>An agentic decision-intelligence platform orchestrating governed supplier disruption mitigation for high-velocity manufacturing.</em></p>

  [![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![React 19](https://img.shields.io/badge/React-19.0-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev/)
  [![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
  [![PostgreSQL / Neon](https://img.shields.io/badge/PostgreSQL-18.6_Neon-4169E1.svg?style=flat&logo=postgresql&logoColor=white)](https://neon.tech/)
  [![Tests: 116 Passed](https://img.shields.io/badge/tests-116%20passed-success.svg?style=flat)](https://github.com/parth022002/ProcuraX)
  [![Regression Gate: PASS](https://img.shields.io/badge/regression%20gate-PASS-brightgreen.svg?style=flat)](https://github.com/parth022002/ProcuraX)
  [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)
</div>

---

## 1. Executive Summary

**ProcuraX** is a governed, agentic AI procurement decision-intelligence platform built for high-stakes supply chain resilience. Traditional enterprise procurement systems are passive record-keepers (ERPs) or generic BI dashboards that flag disruptions only after assembly lines stall. ProcuraX introduces a closed-loop, verifiable decision architecture that detects external supply shocks, quantifies financial runway risk across multi-tier bill-of-materials, solves constrained mitigation options, grounds decisions in legal contracts, and enforces deterministic human-in-the-loop approvals before staging proposals.

The platform is anchored in the flagship scenario of **ApexDrive Components** (a tier-1 automotive supplier) and its critical power-electronics vendor **ElectroPulse Components (`SUP-1047`)**.

```
Signals (GDELT/Marketaux) ──> ML Risk Model ──> Multi-Tier Impact Engine
                                                        │
Human CPO Approval <── Policy Engine (RBAC) <── Scenario Solver (SCN-A..D)
       │
Staged Proposal Packet (SHA-256 Sealed, Zero Live ERP Write-back)
```

---

## 2. Core Architectural Pillars

1. **Separation of Concerns:** 
   - ML predicts probabilities ($P(\text{disruption})$);
   - Governed risk mappers convert predictions to 0–100 operational scores;
   - Deterministic impact engines compute mathematical revenue and inventory runway exposure;
   - Operations solvers compute contractually feasible mitigation scenarios;
   - RAG copilots retrieve and cite binding clauses;
   - Policy engines enforce role-based spend limits (RBAC);
   - Human executives approve material actions;
   - Action packets are cryptographically sealed with SHA-256 and restricted to **proposal-only** staging (`is_proposal_only: True`).
2. **Zero Hallucination of Business Figures:** LLMs are never permitted to generate or guess numerical exposures, contract lead times, or inventory values. All displayed numbers derive from auditable backend services.
3. **Transparent Data Provenance:** Every displayed record is tagged with its provenance classification: `PUBLIC_REAL`, `SYNTHETIC`, `DERIVED`, or `ILLUSTRATIVE`.
4. **Contamination Isolation:** Disruption data for held-out flagship supplier `SUP-1047` is strictly quarantined from model training rows.

---

## 3. The 8-Stage Governed Decision Loop

| Stage | Name | Operational Function | Technology & Governance |
|:---:|:---|:---|:---|
| **01** | **Sense** | Ingests and deduplicates real external news and trade intelligence. | Adapters for GDELT v2, Marketaux, Alpha Vantage, NewsData.io, and SEC EDGAR with SHA-256 deduplication. |
| **02** | **Predict** | Predicts disruption probability with explainable risk drivers. | Calibrated Logistic Regression (`risk-model-calibrated-v1.0`) with ECE tracking and SHAP feature contributions. |
| **03** | **Quantify** | Traverses multi-tier BOM down to plant-level inventory runway. | Topological network traversal calculating gross revenue at risk, shortage units, and plant downtime risk (Pune, Chennai, Greater Noida). |
| **04** | **Simulate** | Evaluates 4 canonical mitigation options against binding contracts. | Constrained solver evaluating MOQ, expedite surcharges, tooling fees, and net avoided loss for SCN-A through SCN-D. |
| **05** | **Ground** | Verifies legal SOPs and agreements with clause-level citations. | RAG retrieval engine with Critic sufficiency evaluation (capped at 1 retry), honest abstention, and prompt injection defense. |
| **06** | **Govern** | Evaluates role-based delegation of authority and spend thresholds. | Deterministic Policy Engine (Planner $\le ₹10\text{L}$, CPO $> ₹10\text{L}$). Blocks unauthorized actions with `HTTP 403`. |
| **07** | **Approve** | Human approval workbench generating proposal-only action packets. | SHA-256 signed proposal packet (`is_proposal_only: True`) staged for ERP review. No live transactional ERP write-back. |
| **08** | **Learn** | Records observed operational KPIs and seals audit history. | Post-decision audit store isolating observed outcomes from prediction training sets for continuous model governance. |

---

## 4. Product Workspace Surfaces

ProcuraX delivers a unified, responsive interface built with the approved **Forest & Copper** visual design system:

* **Executive Control Tower:** Cross-tier disruption overview, macro KPIs, live signal feeds, and domain-specific filters.
* **Supplier 360:** Deep supplier health profile, calibrated risk scorecards, and model card transparency.
* **Impact Map & Network Graph:** Interactive multi-tier BOM dependency visualizer linking suppliers, component SKUs, and assembly facilities.
* **Scenario Studio:** Solver workbench comparing counterfactual baseline (*Do Nothing*), alternate suppliers, air freight expediting, and hybrid mitigation.
* **Evidence Panel & Copilot:** Retrieval workbench with strict clause-level citation cards and honest abstention guardrails.
* **Approvals Workbench:** Human-in-the-loop decision console enforcing RBAC spend limits with cryptographic packet sealing.
* **Outcome Review:** Post-decision operational tracking comparing simulated forecasts against actual OTIF and cost KPIs.
* **Evaluation & Observability Dashboard:** Live model calibration curves, dataset DQ scorecards (8 tables, 0 violations), and provider telemetry.

---

## 5. Technology Stack

### Frontend
- **Framework:** React 19, TypeScript 5.6, Vite 8.3
- **Design System:** Custom Forest & Copper CSS tokens, responsive off-canvas mobile drawer, WCAG 2.2 AA $44\times 44\text{px}$ touch targets
- **State & Networking:** Typed API client with fallback fixtures, zero external component libraries

### Backend
- **Framework:** FastAPI, Python 3.9+, Pydantic v2
- **State Machine:** 11-step typed agent state machine with idempotent case management
- **Security:** In-memory sliding-window rate limiting, distributed correlation tracing (`X-Trace-ID`, `X-Request-ID`), SSRF protection, defense-in-depth security headers
- **Database:** PostgreSQL 18.6 on Neon Serverless with Alembic migration versioning (`alembic upgrade head`)

---

## 6. Quickstart & Local Setup

### Prerequisites
- Python 3.9+ installed
- Node.js 20+ / npm 10+ installed
- Git

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/parth022002/ProcuraX.git
cd ProcuraX

# Copy environment template
cp .env.example .env
```

### 2. Set Up & Run Backend
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations (Neon PostgreSQL)
cd backend
alembic upgrade head
cd ..

# Start backend server (Port 8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
* Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
* Health Endpoint: `http://127.0.0.1:8000/api/v1/health`

### 3. Set Up & Run Frontend
```bash
cd frontend
npm install
npm run dev
```
* Web Application: `http://localhost:5173`

---

## 7. Verification & Automated Quality Gates

ProcuraX is built to rigorous QA standards. The entire test suite and regression pipeline can be executed locally:

```powershell
# 1. Run Complete Backend Test Suite (116 tests across 17 suites)
python -m pytest backend/tests -v

# 2. Run Deterministic 5-Minute Showcase Replay (All 8 Stages)
python scripts/run_decision_loop_replay.py

# 3. Run Master Full Regression Gate (All 7 Validation Stages)
python scripts/full_regression_check.py
```

### Master Quality Gate Verification Summary

```
================================================================================
PROCURAX REGRESSION SCORECARD & RELEASE READINESS REPORT
================================================================================
[PASS]   1. Repository Structure             : All required directories and starter files present
[PASS]   2. Python Compilation               : Syntax & bytecode clean
[PASS]   3. Data Integrity & Leakage         : 8 tables validated, SUP-1047 holdout guard active
[PASS]   4. Backend Tests                    : 116 tests passed in 100%
[PASS]   5. Secret Hygiene                   : Clean scan, zero real credentials committed
[PASS]   6. Showcase Replay                  : All 8 stages (Sense to Learn) passed in 1.40s
[PASS]   7. Frontend Production Build        : TypeScript + Vite production bundle clean (822ms)
--------------------------------------------------------------------------------
OVERALL RESULT: [PASS] -- ALL GATES MET. READY FOR PUBLIC SHOWCASE.
================================================================================
```

---

## 8. Deployment Architecture

### Modern Cloud Deployment (Vercel + Render / Railway)

1. **Backend (Render / Railway / Fly.io):**
   - **Root Directory:** `.`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:**
     - `DATABASE_URL`: Connection string for Neon Serverless PostgreSQL
     - `APP_ENV`: `production`
     - `FRONTEND_ORIGIN`: `https://your-frontend.vercel.app`

2. **Frontend (Vercel):**
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Environment Variable:**
     - `VITE_API_URL`: `https://your-backend.onrender.com`

---

## 9. Documentation Index

Detailed engineering references and architectural specifications are located in [`docs/`](docs/):

* [MASTER_DEVELOPMENT_BRIEF.md](docs/MASTER_DEVELOPMENT_BRIEF.md) — Definitive operational summary of Blueprint v3.5.
* [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Component architecture, state machine, and data flow.
* [API_CONTRACTS.md](docs/API_CONTRACTS.md) — REST endpoint schemas, payloads, and response envelopes.
* [DATABASE.md](docs/DATABASE.md) — Relational schema, indexes, check constraints, and Alembic migrations.
* [DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) — Forest & Copper design tokens, typography, and accessibility guidelines.
* [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) — Step-by-step production operations and hosting runbook.
* [LIMITATIONS_AND_ETHICS.md](docs/LIMITATIONS_AND_ETHICS.md) — Boundaries, honest status definitions, and AI safety protocols.
* [FINAL_REPORT.md](reports/final_verification/FINAL_REPORT.md) — Complete release verification and responsive UX report.

---

## 10. Disclaimer & Ethics

ProcuraX is a Proof-of-Concept decision intelligence platform. While external market and news signals derive from real public endpoints (GDELT, Marketaux, SEC EDGAR), all supplier relationships, internal purchase orders, plant inventory levels, and commercial contracts relating to *ApexDrive Components* are synthetic. ProcuraX strictly prohibits autonomous enterprise purchasing; all generated mitigation actions require human executive approval and are generated for review purposes only.

---

## 11. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
