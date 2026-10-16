# ProcuraX — Final Verification Baseline Audit Report
**Phase A: Pre-Remediation System Inspection & Defect Inventory**
**Audit Date:** 2026-10-16  
**Auditor Role:** Senior QA Lead, Full-Stack Engineer, Accessibility & Security Reviewer  
**Scope Baseline:** Master Blueprint v3.5 & AGENTS.md  

---

## 1. Repository Structure & Route Architecture

### 1.1 Backend Service Structure
- **Framework:** FastAPI with Uvicorn server (`http://127.0.0.1:8000`)
- **API Base:** `/api/v1`
- **Routing Modules (`backend/app/api/v1/routes/`):**
  - `health.py`: Process health (`GET /health`), Database connectivity (`GET /health/database`)
  - `suppliers.py`: Supplier registry (`GET /suppliers`), 360 view (`GET /suppliers/{id}/360`), Performance (`GET /suppliers/{id}/performance`), Contracts (`GET /suppliers/{id}/contracts`)
  - `signals.py`: External signal query (`GET /signals`), Provider health & telemetry (`GET /signals/providers`, `GET /signals/providers/health`), Ingestion trigger (`POST /signals/ingest`)
  - `risk.py`: Calibrated risk prediction (`GET /risk/score`, `POST /risk/score`), Model card metadata (`GET /risk/model-card`)
  - `impact.py`: Supplier impact assessment (`GET /impact/supplier/{id}`), Network graph traversal (`GET /impact/network/{id}`), Impact calculator engine (`POST /impact/calculate`)
  - `scenarios.py`: Scenario generation (`POST /scenarios/generate`), Optimization solver (`POST /scenarios/optimise`), Contractual constraints (`GET /scenarios/constraints/{id}`)
  - `copilot.py`: Evidence retrieval & recommendation (`POST /copilot/recommend`), Document corpus (`GET /copilot/documents`)
  - `cases.py`: Case lifecycle replay (`POST /cases/run`), Case ledger (`GET /cases`), Single case (`GET /cases/{id}`), Case sign-off (`POST /cases/{id}/approve`), Outcome capture (`POST /cases/{id}/outcome`)
- **Core Security & Middleware:**
  - `TraceMiddleware` (`app.core.logging_config`): Generates and propagates `X-Trace-ID` and `X-Request-ID`.
  - `RateLimitMiddleware` (`app.core.rate_limit`): Sliding-window rate limiter with tiered limits (120 req/min general, 30 req/min heavy simulation).
  - `register_error_handlers` (`app.core.error_handlers`): Standardized JSON operational error envelope `{error, detail, status_code, trace_id, timestamp_utc, next_permitted_action}`.
  - `security.py` (`app.core.security`): Cryptographic token verification, `get_current_user`, `require_roles` RBAC role guards, and `enforce_tenant_isolation`.
  - `safe_requests.py` (`app.core.safe_requests`): SSRF protection shield validating provider hostnames against whitelist and blocking private/loopback/cloud metadata (`169.254.169.254`).

### 1.2 Frontend Application Architecture
- **Framework:** React 18 + TypeScript + Vite (`http://127.0.0.1:5173`)
- **Theme:** Forest & Copper enterprise design system (`#1E3A2F` forest green, `#C26D38` copper, `#F7F5F0` warm ivory background)
- **Component & View Mapping (`frontend/src/`):**
  - `PublicLandingPage.tsx`: Public showcase with 8-stage interactive decision pipeline.
  - `ControlTowerView.tsx`: Executive Control Tower with Disruption Hero, domain tabs (`Procurement`, `Logistics`, `Demand`, `Stock`), and active cases ledger.
  - `Supplier360View.tsx`: Flagship supplier `SUP-1047` (ElectroPulse Components), risk radar, and component breakdowns.
  - `ImpactMapView.tsx`: Multi-tier supply chain topological dependency graph and plant runway calculators (Pune, Chennai, Greater Noida).
  - `ScenarioStudioView.tsx`: Solver-backed mitigation candidates (`SCN-A` through `SCN-D`) and sensitivity analysis.
  - `EvidencePanelView.tsx`: Authoritative contract clauses, policy citations, and honest abstention guarantees.
  - `ApprovalWorkbenchView.tsx`: Governed 11-step lifecycle state machine stepper, Proposal-Only Action Packet (`is_proposal_only: True`), and SHA-256 seal.
  - `OutcomeReviewView.tsx`: Post-decision closed-loop learning sliders and append-only audit ledger.
  - `EvaluationDashboardView.tsx`: Calibrated ML ROC-AUC benchmarks, calibration curve, external provider telemetry, and audit trail.
  - `DataSourcesView.tsx` & `IntegrationSettingsView.tsx`: Data provider health indicators and Lakebase PostgreSQL connection monitoring.

### 1.3 Database & Ingestion Architecture
- **Database Engine:** Neon Lakebase Postgres (PostgreSQL 18.6)
- **Migrations:** Alembic versioned migration chain (`0001_initial_core_schema.py`, `0002_signal_persistence_and_provenance.py`)
- **Persistence Store:** `SignalRepository` executing idempotent batch upserts into `external_signals` (`ON CONFLICT (signal_id) DO UPDATE`).

---

## 2. Baseline Build, Compilation & Test Results

```bash
# 1. Bytecode Compilation
python -m compileall -q backend scripts
# Result: 0 syntax errors, 100% clean compilation [PASS]

# 2. Frontend Production Bundle Build
cd frontend && npm run build
# Result: Built cleanly in 888ms (dist/assets/index-*.js 427.65 kB, dist/assets/index-*.css 89.96 kB) [PASS]

# 3. Backend Pytest Suites
python -m pytest backend/tests -q
# Result: 106 passed, 3 warnings in 125.68s (100% PASS)

# 4. Master 7-Gate Quality Gateway
python scripts/full_regression_check.py
# Result: All 7 gates passed in 163.56s [PASS]

# 5. Live Backend Endpoints & Database Audit
python scripts/verify_backend_elements.py
# Result: 18/18 endpoints passed, database connection healthy [PASS]
```

---

## 3. Route-by-Route Defect & Responsive Vulnerability Inventory

| ID | Severity | Route / Surface | Area / Element | Defect Description & Evidence | Steps to Reproduce |
|---|---|---|---|---|---|
| **DEF-01** | **P1 (Critical)** | Workspace Shell (All routes) | Mobile Navigation (`<850px`) | At viewport widths <850px (and especially 320px-430px), `.sidebar` renders as a static block above `.main-area`, taking up extensive vertical height with 9 tabs and forcing users to scroll past the entire menu to reach content. | Resize browser window to 375px width on any workspace view. |
| **DEF-02** | **P1 (Critical)** | Approval Workbench | 11-Stage Lifecycle Stepper (`<600px`) | Stepper uses `grid-template-columns: repeat(4, 1fr)` at `<=850px`. On narrow phone screens (320px-390px), step columns are constrained to ~75px, causing step numbers and titles to truncate, wrap awkwardly, or overflow. | Navigate to Approval Workbench at 360px viewport width. |
| **DEF-03** | **P2 (Major)** | Control Tower & Signals | Table Regional Overflow (`<768px`) | On narrow phone viewports, wide data tables (disruption cases, live news signals) risk causing accidental global horizontal overflow (`document.documentElement.scrollWidth > window.innerWidth`) if table wrappers lack strict localized `overflow-x: auto`. | Inspect `document.documentElement.scrollWidth` at 320px width on Control Tower and Data Sources views. |
| **DEF-04** | **P2 (Major)** | Executive Topbar | Header Controls (`<600px`) | At widths below 600px, `.topbar-right` containing `.role-capsule-card`, `.tenant-badge`, and action buttons stacks into multiple rows without vertical breathing room, colliding with `.topbar-copilot-search`. | View Control Tower at 375px width. |
| **DEF-05** | **P2 (Major)** | Public Landing Page | 8-Stage Pipeline (`<640px`) | The 8-stage interactive horizontal stepper connector line and stage buttons compress heavily on mobile screens (<430px), requiring clean touch target padding ($\ge 44\times 44\text{px}$) and touch-friendly scrolling. | Open public landing page at 320px width. |
| **DEF-06** | **P3 (Polish)** | Touch Controls | All Forms & Sliders | Primary interactive controls (sliders in Outcome Review, scenario selection radio buttons, tab chips) should strictly adhere to WCAG 2.2 AA target size ($\ge 44\times 44\text{px}$) for touch interactions. | Test touch targets on touch emulation. |

---

## 4. Live API & External Provider Status

| Provider | Category | Auth Header Configured | Last Test Fetch | Status | Safe Handling & Circuit Breaker |
|---|---|:---:|---|:---:|---|
| **GDELT Project** | Global News / Geopolitics | Not Required (Public) | Live (200 OK) | **HEALTHY** | Whitelisted in SSRF shield; rate-limited; offline fallback fixture |
| **Marketaux** | Financial & Supply Chain | Optional API Key | Live (200 OK) | **HEALTHY** | Fallback to canonical fixture on 429/timeout; secret never in client |
| **Alpha Vantage** | Commodity & Logistics | Optional API Key | Live (200 OK) | **HEALTHY** | Fallback to canonical fixture on 429/timeout; secret never in client |
| **NewsData.io** | Industrial & Factory Events | Optional API Key | Live (200 OK) | **HEALTHY** | Fallback to canonical fixture on 429/timeout; secret never in client |
| **SEC EDGAR** | Regulatory & Filings | User-Agent Required | Live (200 OK) | **HEALTHY** | Verified compliant User-Agent headers; SSRF whitelist enforced |

---

## 5. Ordered Remediation Plan

1. **Step 1: Mobile Collapsible Drawer & Hamburger Shell (Fixes DEF-01, DEF-04):**
   - Implement an accessible mobile toggle button (`aria-label="Toggle navigation"`, `aria-expanded`) and slide-in drawer for screen widths $\le 850\text{px}$.
   - Ensure the main content area occupies full mobile viewport width without sidebar pushing.
2. **Step 2: Responsive Stepper Adaptation (Fixes DEF-02, DEF-05):**
   - Refactor `.stepper-horizontal` into a clean horizontally-scrollable or compact status tracker on screens $\le 600\text{px}$.
   - Guarantee 44×44px touch targets on stage buttons with centered indicator dots.
3. **Step 3: Strict Horizontal Overflow Guard & Table Cards (Fixes DEF-03):**
   - Apply localized `overflow-x: auto` wrappers with `-webkit-overflow-scrolling: touch` around all tables.
   - Enforce `max-width: 100vw; overflow-x: hidden;` on body/root to ensure `document.documentElement.scrollWidth === window.innerWidth`.
4. **Step 4: WCAG 2.2 AA Touch Target & Contrast Audit (Fixes DEF-06):**
   - Ensure all buttons, links, inputs, and sliders meet the 44×44px touch target guideline.
   - Verify visible focus rings (`:focus-visible`) across all interactive elements.
5. **Step 5: Viewport Verification Matrix Execution:**
   - Test across all required viewport widths: **320px, 360px, 375px, 390px, 430px, 600px, 768px, 820px, 1024px, 1280px, 1366px, 1440px, 1600px, 1920px**.
   - Verify 200% zoom and prefers-reduced-motion compatibility.
