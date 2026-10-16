# ProcuraX — Agentic Supply Chain Decision Intelligence

**This is a starter repository, not a completed ProcuraX implementation.** It follows the supplied v3.5 blueprint and Vibe Coding checklist. Core business endpoints return explicit `501 Not Implemented` until their sprint is implemented and tested. The dashboard uses clearly labelled illustrative data.

## Quick start

### Requirements
- Python 3.11 or newer.
- Node.js 22.12+ recommended for the current Vite toolchain.
- Git.
- Optional: Docker Desktop for local PostgreSQL/pgvector and Redis.

### 1. Configure environment
```bash
cp .env.example .env
```
On Windows PowerShell:
```powershell
Copy-Item .env.example .env
```
The defaults allow the health endpoint to run without an LLM key or database connection. Never commit `.env`.

### 2. Start backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```
Open `http://127.0.0.1:8000/docs` for the API docs and `http://127.0.0.1:8000/api/v1/health` for the health check.

### 3. Start frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
Open the URL Vite prints, normally `http://localhost:5173`. The current UI is an illustrative shell; data is not connected to a real model/API yet.

### 4. Generate deterministic synthetic data
From the repository root after installing backend dependencies:
```bash
python scripts/generate_synthetic_data.py --out data/generated --seed 42 --scale small
```
Default `--scale small` creates a laptop-friendly dataset and `checksums.txt`. All output is synthetic. The injected ApexDrive disruption is a held-out demo scenario and must not enter training rows.

### 5. Optional local infrastructure
```bash
docker compose up -d postgres redis
```
The local database is exposed on `localhost:5433` to avoid clashing with a local PostgreSQL service. The starter does not automatically apply `backend/app/db/schema.sql`; apply/convert it to migrations only after reviewing `docs/DATABASE.md`.

### 6. Tests
```bash
cd backend
pytest
```
Frontend production build:
```bash
cd frontend
npm run build
```

## Repository guide
- `PROJECT.md`: scope, outcomes, constraints, and current truth.
- `AGENTS.md`: durable instructions for Codex/Cursor/other coding agents.
- `docs/`: requirements, journeys, architecture, data, APIs, design, milestones, testing, decisions and open items.
- `backend/`: FastAPI app, typed endpoints, service utilities, SQL schema and tests.
- `frontend/`: React/Vite TypeScript dashboard shell.
- `scripts/generate_synthetic_data.py`: reproducible synthetic dataset generator.
- `data/`: generated/raw/processed data; generated data should not be committed unless explicitly intended and scrubbed.

## Definition of honest status
- **Implemented:** code exists and its acceptance criteria have passed.
- **Scaffolded:** boundary/file/API shape exists but business logic is incomplete.
- **Illustrative:** synthetic or mock values only.
- **Not verified:** no test/evidence has established the behavior.

See `docs/BUILD_STATUS.md` before assuming any feature is finished.


## Website refresh (v2)
The frontend now opens to a responsive ProcuraX product website with a light-first palette, a contained neon hero visual, subtle CSS motion, a clickable eight-stage decision loop, an illustrative control-tower preview, interactive mitigation scenario selection, and a governed Critic workflow visual. The existing workspace shell remains available from the “Workspace preview” / “Explore the control tower” actions.

The hero and scenario values are illustrative. This refresh does not implement the missing business APIs or represent the PoC as production-ready. See `docs/DESIGN_SYSTEM.md` and `docs/BUILD_STATUS.md`.


## Vibe-coding handoff (read first)
1. Open this folder as the workspace in Codex, Cursor, Antigravity or another coding agent.
2. Start with `MASTER_CODING_AGENT_PROMPT.md`; it requires a repository audit before editing.
3. Use `docs/MASTER_DEVELOPMENT_BRIEF.md` as the detailed execution contract, `docs/ACCEPTANCE_TEST_PLAN.md` as the quality gate, and `docs/DATA_AND_CONNECTORS.md` for public news/market integrations.
4. The v3.5 blueprint is included in `reference/` and remains frozen source truth.
5. The website and workspace shell do not mean the full decision workflow is already implemented. Check `docs/BUILD_STATUS.md` and verify every feature.

## Real data vs fictional operations
The public-source connector starters are in `integrations/real_data_connectors/`. They are a reference integration kit and are not yet fully connected to app persistence, provider settings UI or the agent workflow. Use real public article metadata/market feeds where configured, and synthetic internal ApexDrive operations. Label `PUBLIC_REAL`, `SYNTHETIC`, `DERIVED`, and `ILLUSTRATIVE` data separately. Never put keys in frontend code or commit `.env`.
