# ProcuraX — Project Brief

## 1. Overview
- **Name:** ProcuraX
- **Full title:** ProcuraX — Agentic AI-Driven Supply Chain & Procurement Decision Intelligence Platform
- **One-sentence description:** A governed decision-intelligence PoC that detects supplier disruption risk, quantifies operational/financial exposure, compares feasible mitigation scenarios, grounds recommendations in evidence, routes material actions through human approval, and records outcomes.
- **Primary build wedge:** Supplier disruption decision intelligence.
- **Project type:** Academic PoC / portfolio project.
- **Primary users:** Procurement Manager, Supply Chain Planner, CPO/Executive, Finance/Risk reviewer, Data/System Admin.
- **Source of truth:** The supplied *ProcuraX PoC Build & Showcase Master Blueprint v3.5 (frozen baseline)*. Do not expand the core scope without build evidence and an explicit decision.

## 2. Business problem
Supplier, purchase-order, inventory, supplier-performance, contract/policy, and external-disruption information is fragmented. Teams need a traceable path from a signal to risk, impact, feasible mitigation, evidence, approval, action packet, and outcome.

## 3. Goal and success
A reviewer must be able to replay one supplier-disruption case end to end and inspect:
1. What triggered the case and which sources support it.
2. The risk prediction/score, model version, and drivers.
3. Impact calculations, assumptions, affected SKUs/plants, and inventory runway.
4. Three or more feasible mitigation options with constraints and objective values.
5. Evidence-grounded recommendation with citations or explicit abstention.
6. Deterministic policy enforcement and required human approval.
7. An audit record and post-decision outcome capture.

Success thresholds must be frozen before the final benchmark; do not invent or backfill success metrics after observing results.

## 4. MVP scope
### Must build
- Reproducible synthetic data and data-quality checks.
- Supplier/entity data foundation and API contracts.
- Baseline risk model with temporal validation and leakage controls.
- External signal ingestion/extraction/entity resolution with provenance.
- Explainable risk scoring with a documented distinction between ML probability and governed 0–100 risk score.
- Business impact calculations and dependency traversal.
- Feasible mitigation scenarios and deterministic optimisation/constraint checks.
- RAG over representative contracts/policies with source metadata, citations, evaluation, and abstention.
- One governed agent workflow with trigger-dependent hypotheses, a shared Critic mechanism, one targeted retry maximum, and escalation when evidence remains insufficient.
- Deterministic policy engine / RBAC; the Critic/LLM never authorises actions.
- Approval workbench, append-only audit records, outcome capture.
- Evaluation/observability evidence and a reproducible flagship replay.

### Demonstration surfaces
- Executive Control Tower
- Supplier 360
- Impact Map
- Scenario Studio
- Evidence Panel
- Approval Workbench
- Outcome Review
- Evaluation Dashboard

### Out of scope for this PoC
- Full ORION multi-vertical/multi-agent Control Tower.
- SME advertising/market-growth intelligence domain from BizPilot AI.
- Production ERP/procurement transaction execution or autonomous high-value purchasing.
- Complete digital twin, enterprise SaaS hardening, or production-scale Kubernetes/autoscaling claims.
- Logistics/transport/warehouse/dark-store expansions beyond what is needed to represent supplier-disruption data and the roadmap.

## 5. Architecture decisions for this starter
These are working implementation defaults, not claims that the whole platform is complete:
- Backend: Python + FastAPI.
- Frontend: React + Vite + TypeScript.
- Data: PostgreSQL; pgvector for document embeddings when the embedding model/dimension is selected.
- Dataset: CSV/Parquet synthetic data with fixed seed, as-of date, schema and checksums.
- ML: scikit-learn baseline first; XGBoost/LightGBM candidate only after a baseline and temporal split are working.
- Optimisation: OR-Tools or equivalent deterministic solver; keep solver outputs separate from LLM generation.
- Agent: typed state-machine workflow; one shared Critic contract with context-specific policies.
- LLM: provider adapter with rule-based fallback. No real provider key is required for the scaffold.
- Tests: pytest for backend, frontend production build, and end-to-end replay as the project matures.

## 6. Constraints and safety
- Synthetic/illustrative values must be labelled as such.
- Flagship injected degradation must remain held out from model training.
- The LLM cannot originate or alter numerical outputs used by the risk, impact, solver, or policy layers.
- The Critic evaluates evidence; only the deterministic Policy Engine/RBAC layer authorises actions.
- Insufficient evidence after one targeted retry must abstain/escalate, never silently proceed.
- Never commit secrets. `.env.example` contains placeholder values only.
- Do not claim production readiness, customer outcomes, savings, or measured ROI without evidence.

## 7. Current status
- **Created by this starter kit:** repository structure, docs, minimal FastAPI health endpoint, illustrative frontend shell, synthetic-data generator, small unit tests, SQL schema draft, CI workflow.
- **Not yet implemented:** the core risk-training/evaluation pipeline, signal connectors, full data-quality/entity resolution, impact API, scenario optimiser, production RAG, agent orchestration, approval persistence, evaluation dashboard backed by real runs, and deployment verification.
- **Next action:** complete Sprint 0/1 acceptance gates before implementing the rest of the product.


## Development handoff update (2026-10-14)
- Detailed implementation requirements: `docs/MASTER_DEVELOPMENT_BRIEF.md`.
- Real news/market provider design: `docs/DATA_AND_CONNECTORS.md`.
- Acceptance gates: `docs/ACCEPTANCE_TEST_PLAN.md`.
- Copy/paste coding-agent prompt: `MASTER_CODING_AGENT_PROMPT.md`.
- The architecture and scope in v3.5 remain frozen. Use the current refresh only as the visual starting point; backend/ML/agent features must pass acceptance checks before marked complete.
