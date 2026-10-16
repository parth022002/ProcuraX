# API contracts (v1)

Base URL: `/api/v1`. JSON requests/responses unless stated otherwise. Every error should use a consistent JSON `detail` and a trace/correlation ID when implemented. Do not return success for endpoints whose business logic is still a stub.

| Method | Path | Purpose | Current scaffold status |
|---|---|---|---|
| GET | `/health` | Health/readiness signal | Implemented (process-level only) |
| GET | `/suppliers/{id}/360` | Supplier 360 view | Contract/stub; returns 501 |
| POST | `/signals/ingest` | Ingest approved signal, preserve provenance, resolve entities | Implemented |
| POST | `/risk/score` | Score supplier/order with model version/drivers | Implemented |
| POST | `/impact/calculate` | Calculate exposure/runway/assumptions | Implemented |
| GET | `/impact/supplier/{id}` | Get full supplier network impact report | Implemented |
| GET | `/impact/network/{id}` | Get topological network dependency graph | Implemented |
| POST | `/scenarios/generate` | Generate named mitigation candidates | Implemented |
| POST | `/scenarios/optimise` | Rank feasible scenarios/objective values | Implemented |
| GET | `/scenarios/constraints/{id}` | Get validated contract & policy constraints | Implemented |
| POST | `/copilot/recommend` | Grounded recommendation + citations + abstention | Implemented |
| GET | `/copilot/documents` | List authorized documents filtered by user role | Implemented |
| POST | `/cases/run` | Execute 11-step governed state machine decision loop | Implemented |
| GET | `/cases` | List all disruption cases in audit store | Implemented |
| GET | `/cases/{id}` | Get case detail, audit trail, scenario choices, action packet | Implemented |
| POST | `/cases/{id}/approve` | Human decision with reason, role check, idempotency | Implemented |
| POST | `/cases/{id}/outcome` | Capture observed post-decision operational KPIs | Implemented |
| POST | `/evaluation/run` | Run benchmark and return run ID/metrics | Contract/stub; returns 501 |


## Design rules
- Use request/response schemas (Pydantic) rather than arbitrary untyped dictionaries for implemented endpoints.
- Validate identifiers, enumerations, numeric ranges, dates and financial units.
- Version breaking changes under `/api/v2`; do not silently redefine a field.
- Material action endpoints require authenticated actor, authorization, approval status and audit event.
- Approval endpoints must be idempotent and state-checked; rejection/modify/request-evidence reasons are required.
- Never accept a client-supplied `is_authorized=true` as authority.
- Risk probability, governed score, impact, scenario objective and Critic support are distinct fields with different semantics.
- RAG responses include citation/source metadata and `abstained: true|false`.
- Endpoint response objects and examples will be completed as each sprint is implemented; do not invent schemas beyond this contract.
