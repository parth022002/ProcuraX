# Requirements and acceptance criteria

## Product boundary
The flagship is supplier disruption risk and mitigation decision intelligence for manufacturing/appliance-style operations. The broader logistics/transportation/warehouse/dark-store capability remains roadmap, as does full ORION multi-agent scale-out.

## Functional requirements
| ID | Capability | Priority | Acceptance criteria |
|---|---|---|---|
| FR-01 | Signal ingestion | Must | Ingest permitted RSS/public/regulatory/supplier-announcement inputs; retain source, URL, timestamp, fetch status. |
| FR-02 | Event extraction | Must | Extract event type, material/region/supplier, timestamp and disruption indicators; persist confidence and errors. |
| FR-03 | Entity resolution | Must | Map names to stable internal supplier/region/material identifiers; report match confidence and unresolved records. |
| FR-04 | Supplier feature pipeline | Must | Generate OTIF, lead-time, quality, capacity, concentration, inventory and network features at a documented prediction cutoff. |
| FR-05 | Risk model | Must | Establish a baseline, evaluate a candidate on a temporal holdout, store model/version/drivers, and clearly distinguish probability from governed 0–100 risk score. |
| FR-06 | Business impact engine | Must | Traverse supplier → material → plant → SKU relationships and return exposure/runway with versioned formulas and assumptions. |
| FR-07 | Scenario engine | Must | Produce 3–4 named candidate mitigations, including do-nothing baseline, alternate supplier, expedite/inventory, and hybrid. |
| FR-08 | Optimisation | Must | Enforce capacity, MOQ, contracts, lead-time and service constraints; reconcile objective; handle infeasibility explicitly. |
| FR-09 | RAG copilot | Must | Retrieve approved contract/policy evidence, cite sources, enforce access filtering, and abstain when evidence is insufficient. |
| FR-10 | Governed procurement agent | Must | Orchestrate detect → investigate → options → brief → approval → outcome with typed states/tools. |
| FR-11 | Approval workbench | Must | Approve, modify, request more evidence, reject or escalate; enforce role/threshold server-side. |
| FR-12 | Audit trail | Must | Append decision/event records with actor, timestamps, evidence refs, versions and approval reason. |
| FR-13 | Control tower | Demo | Risk × exposure prioritisation, trend and drill-down to supplier/PO/SKU/plant. |
| FR-14 | Evaluation dashboard | Demo | Show model, signal, impact, optimisation, RAG, agent, system and business metrics from actual run records. |
| FR-15 | Learning capture | Must | Store outcome separately from prediction-time features; label only after the outcome is observed. |

## Non-functional requirements
- Reproducibility: dataset seed/config/schema/checksums, versioned model/prompt/retriever/solver configuration, run ID and commit SHA.
- Integrity: prediction-time features never contain future actual delivery/quality/outcome data.
- Governance: the Critic evaluates evidence; deterministic Policy Engine/RBAC authorises; human approval is required for material actions.
- Agent behavior: activate hypotheses from observed triggers; allow one targeted follow-up only; after a failed second Critic check, abstain/escalate.
- Reliability: API errors are typed and actionable; unimplemented endpoints do not pretend to succeed.
- Observability: track trace/case ID, model version, stage timing, tool failures, LLM tokens/cost where applicable.
- Accessibility/responsiveness: keyboard focus, semantic labels, legible charts/tables, responsive desktop/tablet layouts.
- Claims: synthetic/illustrative results must be labelled; no customer/production/ROI claims without evidence.

## Role boundaries
- Procurement Manager: investigate, compare scenarios, submit decisions within allowed policy.
- Supply Chain Planner: assess plant/SKU exposure and inventory/transfer options.
- Executive/Decision Owner: approve material decisions within configured thresholds.
- Finance/Risk: inspect assumptions, exposure and audit evidence.
- Admin: configure users/integrations/policies; administrative privileges do not bypass audit logging.

## Out of scope
- Autonomous high-value purchasing.
- Production ERP transaction execution.
- Generic chatbot as the primary experience.
- Using sentiment alone as supplier-risk truth.
- Kubernetes/Kafka/feature-store complexity unless justified by a tested requirement.
- Advertising analytics/SME revenue-growth features.


## Additional development requirements — real public signals / fictional operations
| ID | Capability | Priority | Acceptance criteria |
|---|---|---|---|
| FR-16 | Provenance labeling | Must | Every material record is labelled PUBLIC_REAL, SYNTHETIC, DERIVED or ILLUSTRATIVE, and UI shows the label where it affects a decision. |
| FR-17 | Provider management | Must | Provider status/freshness/last fetch/result/error/quota is explicit; secrets never leave backend. |
| FR-18 | News normalization and deduplication | Must | Common signal schema, canonical URL/title dedupe, separate publish/retrieval timestamps and source links. |
| FR-19 | Sentiment/event separation | Must | Provider sentiment, internal sentiment, event severity, entity mapping, evidence confidence and risk score are separate fields. |
| FR-20 | Fictional scenario mapping | Must | Public signal-to-ApexDrive linkage is an explicit, auditable scenario assumption; it cannot be misrepresented as a real supplier relationship. |
| FR-21 | Provider failure state | Must | Unconfigured, no-results, quota-exceeded, rate-limited and provider-unavailable are visibly distinct. |
| FR-22 | Versioned decision replay | Must | Case replay records input data snapshot, model, prompt/retriever, solver, policy and schema versions. |
