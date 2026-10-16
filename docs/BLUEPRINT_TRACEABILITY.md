# Traceability: ProcuraX v3.5 blueprint → starter files

| Blueprint area | Where represented in this repository | Implementation status here |
|---|---|---|
| Executive summary, scope and success definition (Sections 1–4) | `PROJECT.md`, `docs/REQUIREMENTS.md` | Documented; scope frozen to supplier disruption |
| Personas and journey (Section 5) | `docs/USER_FLOWS.md` | Documented; UI is an illustrative shell |
| Sense-to-learn loop (Section 6) | `docs/ARCHITECTURE.md` | Documented; not yet fully wired at runtime |
| Functional requirements FR-01–FR-15 (Section 7) | `docs/REQUIREMENTS.md` | Acceptance criteria captured; most features remain unimplemented |
| Architecture layers (Section 8) | `docs/ARCHITECTURE.md` | Design represented; minimal API only |
| Data foundation (Section 9) | `docs/DATABASE.md`, `backend/app/db/schema.sql` | Schema draft + generator; migrations/load pipeline remain |
| Synthetic data and leakage controls (Section 10, Appendix E) | `scripts/generate_synthetic_data.py`, `docs/TESTING.md` | Generator implemented; temporal split/training pipeline remains |
| Feature engineering and risk model (Sections 11–12) | `docs/REQUIREMENTS.md`, `docs/TESTING.md`, `docs/DECISIONS.md` | Not implemented yet; target horizon and score mapping remain open |
| External signal intelligence (Section 13) | `docs/REQUIREMENTS.md`, API stub | Not implemented yet |
| Business impact / dependency engine (Section 14) | `backend/app/services/impact_engine.py` | Formula utility prototype with unit tests; not connected to data/API |
| Constraint extraction and optimisation (Section 15) | `docs/USER_FLOWS.md`, `docs/ARCHITECTURE.md`, API stubs | Not implemented; solver and constraint validation remain |
| RAG and Agentic RAG (Section 16) | `docs/REQUIREMENTS.md`, `docs/USER_FLOWS.md` | Not implemented yet |
| Governed agent, Critic, retry and escalation (Section 17) | `backend/app/services/critic.py`, `docs/ARCHITECTURE.md` | Composite support utility implemented; workflow/retrieval not wired |
| Governance, Security and Responsible AI (Section 18) | `backend/app/services/policy_engine.py`, `docs/SECURITY_AND_DATA.md` | Minimal policy utility tested; authentication/persistence not implemented |
| MLOps / LLMOps (Sections 19–20) | `docs/TESTING.md`, `docs/IMPLEMENTATION_PLAN.md` | Design/acceptance notes only |
| Stack/build choices (Section 21) | `backend/pyproject.toml`, `frontend/package.json`, `docker-compose.yml` | Foundation dependencies/config scaffolded |
| API contract (Section 22) | `docs/API_CONTRACTS.md`, `backend/app/api/v1/routes/` | Health implemented; business routes return explicit HTTP 501 |
| UX/screen spec (Section 23) | `docs/USER_FLOWS.md`, `docs/DESIGN_SYSTEM.md`, `frontend/src/App.tsx` | Illustrative UI only; core user flows not connected |
| Observability, data model, evaluation/counterfactual/robustness (Sections 24–28) | `docs/DATABASE.md`, `docs/TESTING.md` | Specifications captured; runtime evidence not present |
| Testing and quality gates (Section 29) | `docs/TESTING.md`, `backend/tests/` | Smoke and small utility unit tests included; integration/E2E not implemented |
| Ten sprints and repository structure (Sections 30–32) | `docs/IMPLEMENTATION_PLAN.md`, `docs/REPOSITORY_STRUCTURE.md` | Plan and scaffold provided |
| Demo runbook, dashboard, showcase/resume (Sections 33–37) | `docs/BUILD_STATUS.md`, `docs/IMPLEMENTATION_PLAN.md` | Future tasks; no claim of finished demo evidence |
| Risks and ORION roadmap (Sections 38–39) | `PROJECT.md`, `docs/DECISIONS.md` | Scope boundary recorded |
| Definition of Done (Section 40) | `docs/TESTING.md`, `docs/IMPLEMENTATION_PLAN.md` | Acceptance rules captured; final DoD not yet passed |

This table is a navigation aid, not evidence of feature completion. Use `docs/BUILD_STATUS.md` for the honest current status.
