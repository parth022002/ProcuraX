# ProcuraX Post-Update Audit, Hardening & Verification Baseline Report

**Audit Date**: 16 October 2026  
**Auditor**: Lead Full-Stack, Security, ML & Release Engineering Subsystem  
**Baseline Document**: Frozen ProcuraX Master Blueprint v3.5 & Operational Brief  
**Active Git Commit**: `65794a37a61dfde879aba9be2fa69440040d5af9` (Branch: `main`, Working tree: Clean)  
**Live Target Deployments**:  
- Frontend: `https://procurax-five.vercel.app`  
- Backend: `https://procurax-api.onrender.com`  

---

## 1. Executive Status & Verification Matrix

### 1.1 Status Categories
- **Confirmed Working**: Implemented in source, backed by automated tests, verified locally and in production.
- **Fixed in Latest Remediation**: Auto-case execution removed from Approvals page load; OpenAPI security schemes declared; metrics reconciled to ₹36.45 Cr / 1.41d / 39.7 / 87.1%; workspace URL hash routing active.
- **Remaining P0/P1 Defects**: Slow synchronous provider calls in `GET /signals` read path; sequential provider fetching; lack of auth on `/signals/scrape` and `/cases/{id}/outcome`; static champion metrics in benchmark analytics not tied to active model registry; hardcoded latency fallbacks in IntegrationSettingsView; unseeded default case in fresh database.

---

## 2. Feature Traceability & Lineage Matrix

| Feature / Workspace Surface | Frontend Component | Primary API Route | Backend Service | Storage / Engine | Test Coverage |
|---|---|---|---|---|---|
| **Executive Control Tower** | `ControlTowerView.tsx` | `GET /api/v1/signals`<br>`GET /api/v1/signals/providers` | `signal_service` | PostgreSQL `external_signals` + In-Memory | `test_signal_intelligence.py` (PASS) |
| **Supplier 360 & Risk** | `Supplier360View.tsx` | `POST /api/v1/risk/score`<br>`GET /api/v1/risk/model-card` | `compute_supplier_features`, `SupplierRiskModel` | Serialized Model `models/registry/logistic_model.pkl` | `test_risk_model.py` (PASS) |
| **Impact Network Graph** | `ImpactMapView.tsx` | `GET /api/v1/impact/supplier/{id}`<br>`GET /api/v1/impact/network/{id}` | `impact_service` | Deterministic MILP BOM network traversal | `test_impact_engine.py` (PASS) |
| **Scenario Studio** | `ScenarioStudioView.tsx` | `POST /api/v1/scenarios/generate`<br>`POST /api/v1/scenarios/optimise` | `scenario_service` | Deterministic Solver + Constraints | `test_scenarios.py` (PASS) |
| **Evidence & RAG Copilot** | `EvidencePanel.tsx` | `POST /api/v1/copilot/recommend`<br>`GET /api/v1/copilot/documents` | `rag_service`, `Critic` | In-Memory FAISS/Vector + Governance Docs | `test_rag_copilot.py` (PASS) |
| **Approval Workbench** | `ApprovalWorkbenchView.tsx` | `POST /api/v1/cases/run`<br>`POST /api/v1/cases/{id}/approve` | `case_service`, `PolicyEngine` | PostgreSQL `cases` + Append-only Audit Log | `test_agent_orchestrator.py` (PASS)<br>`test_security_rbac.py` (PASS) |
| **Post-Decision Outcome** | `OutcomeReviewView.tsx` | `POST /api/v1/cases/{id}/outcome` | `case_service.record_outcome` | PostgreSQL `cases.metadata` | `test_agent_orchestrator.py` (PASS) |
| **System Integrations** | `IntegrationSettingsView.tsx`| `GET /api/v1/health/database`<br>`GET /api/v1/signals/providers` | `check_db_health`, `signal_service` | Neon Postgres Connection Pool | `test_health.py` (PASS) |
| **Evaluation Benchmarks** | `EvaluationDashboardView.tsx`| `GET /api/v1/models/benchmark`<br>`GET /api/v1/risk/model-card` | `SupplierRiskModel`, `analytics` | Static vs Model Card Registry | `test_risk_model.py` (PASS) |

---

## 3. API Security & Access Control Classification

| Route | HTTP Method | Required Role / Auth | Object-Level Guard | Security Scheme in OpenAPI |
|---|---|---|---|---|
| `/api/v1/health` | GET | Public Read-Only | None | None |
| `/api/v1/health/database` | GET | Public Read-Only (Diagnostics) | None | None |
| `/api/v1/suppliers` | GET | Public Read-Only | None | None |
| `/api/v1/signals` | GET | Public Read-Only | None | None |
| `/api/v1/signals/providers` | GET | Public Read-Only | None (Redacted secrets) | None |
| `/api/v1/signals/ingest` | POST | Privileged Mutation (`ADMIN`, `CPO`, `PROCUREMENT_MANAGER`) | Rate-limited | `BearerAuth` / `ApiKeyAuth` |
| `/api/v1/signals/scrape` | POST | **Defect**: Missing auth dependency | Rate-limited | **To Fix in Phase 1**: Require Role |
| `/api/v1/cases` | GET | Authenticated Read | Tenant Isolation | `BearerAuth` |
| `/api/v1/cases/{case_id}` | GET | Authenticated Read | Tenant Isolation | `BearerAuth` |
| `/api/v1/cases/run` | POST | Authenticated Mutation | Tenant Isolation | `BearerAuth` |
| `/api/v1/cases/{id}/approve`| POST | Privileged Mutation (Policy RBAC clamped) | Role Rank Hierarchy | `BearerAuth` |
| `/api/v1/cases/{id}/outcome`| POST | **Defect**: Missing auth dependency | Tenant Isolation | **To Fix in Phase 1**: Require Role |
| `/api/v1/copilot/recommend` | POST | Authenticated Read | Role-level doc filter | `BearerAuth` |

---

## 4. Top P0/P1 Defects & Root Causes

1. **Defect P0.1 — Missing Authentication on Mutation Endpoints**:
   - Files: `backend/app/api/v1/routes/cases.py` (`POST /cases/{case_id}/outcome`), `backend/app/api/v1/routes/signals.py` (`POST /signals/scrape`).
   - Root Cause: Missing `Depends(get_current_user)` or `Depends(require_roles(...))` on route signatures.
   - Fix: Add explicit role requirement (`require_roles(["ADMIN", "CPO", "PROCUREMENT_MANAGER"])`).

2. **Defect P0.2 — Inconsistent OpenAPI Security Scheme Operation References**:
   - Files: `backend/app/core/security.py`, `backend/app/main.py`.
   - Root Cause: `HTTPBearer(auto_error=False)` by default attaches schema name `"HTTPBearer"` rather than `"BearerAuth"`.
   - Fix: Pass `scheme_name="BearerAuth"` to `HTTPBearer` so operation references align with `securitySchemes["BearerAuth"]`.

3. **Defect P0.3 — Slow Synchronous Provider Ingestion on Read Endpoint**:
   - Files: `backend/app/api/v1/routes/signals.py`, `backend/app/services/signal_intelligence/service.py`.
   - Root Cause: When `settings.enable_live_signals=True`, `GET /signals` calls `signal_service.ingest_signals()`, synchronously blocking for 20+ seconds over external APIs.
   - Fix: Separate reading persisted/cached signals (`repository.fetch_persisted_signals()`) from live fetching. Live ingestion is only triggered via `POST /signals/ingest` or explicit refresh. Parallelize provider calls using a thread pool.

4. **Defect P1.1 — Database Health Query Overhead & Hardcoded Fallbacks**:
   - Files: `backend/app/db/session.py`, `frontend/src/components/IntegrationSettingsView.tsx`.
   - Root Cause: `check_db_health()` executed 4 sequential roundtrips over non-pooled connection (`SELECT version()`, `count(suppliers)`, `count(skus)`, `count(inventory)`). Frontend hardcoded fallback `14.2 ms` and `PostgreSQL 16.2`.
   - Fix: Combine DB checks into a single composite query. Remove hardcoded fallback in UI and show measured dynamic values.

5. **Defect P1.2 — Disconnect between Active ML Model and Benchmark Leaderboard**:
   - Files: `backend/app/api/v1/routes/analytics.py`, `frontend/src/components/EvaluationDashboardView.tsx`.
   - Root Cause: `analytics.py` returned a hardcoded mock leaderboard where Champion was an uncalibrated Ensemble, while inference model is `ProcuraX-Disruption-Logistic` (`risk-model-calibrated-v1.0`).
   - Fix: Ensure `analytics.py` dynamically reports the actual registered models from `models/registry/` and marks synthetic provenance prominently.

---

## 5. Phased Execution Plan

### Phase 1: P0 Security, Identity & Side-Effect Controls
- Add `Depends(require_roles(...))` to `POST /cases/{case_id}/outcome` and `POST /signals/scrape`.
- Set `scheme_name="BearerAuth"` in `HTTPBearer` so OpenAPI operation-level security matches `components.securitySchemes`.
- Add test in `test_security_rbac.py` verifying that unauthenticated calls to `/signals/scrape` and `/cases/{id}/outcome` return 401/403.

### Phase 2: Canonical Case & Metrics Lineage
- Ensure baseline case `CAS-SUP-1047-01` is seeded on startup or available in PostgreSQL so `GET /cases` returns the persisted flagship case.
- Clearly label `Incident ID: DISR-2026-1047` vs `Governed Case ID: CAS-SUP-1047-01`.
- Add visual indicator for `Snapshot Date: 2026-09-30 (Historical Replay Mode)`.

### Phase 3: Signals Reliability, Latency & Asynchronous Jobs
- Decouple `GET /api/v1/signals` from synchronous external provider fetching (read from DB/cache in <100ms).
- Parallelize external provider requests in `SignalIntelligenceService.ingest_signals()` with `ThreadPoolExecutor(max_workers=5)` and individual 5s timeouts.
- Add background job execution support for `POST /api/v1/signals/ingest`.

### Phase 4: ML Inference & Benchmark Registry Alignment
- Align `GET /api/v1/models/benchmark` with actual registered model cards in `models/registry/`.
- Ensure active model card explicitly states `PROVENANCE: SYNTHETIC BENCHMARK` and displays exact evaluation metrics.

### Phase 5: Workspace UX, Responsive Performance & Typography
- Fix hardcoded latency / version fallbacks in `IntegrationSettingsView.tsx`.
- Reflow cards and tables for viewports 320px–1920px without horizontal scroll or clipping.
- Verify live fetch progress indicator resets cleanly upon job completion.

### Phase 6: Release Candidate Verification & Final Report
- Run all 116+ backend pytest tests.
- Run frontend production build (`npm run build`).
- Verify live API endpoints.
- Generate final release report per Section 13.
