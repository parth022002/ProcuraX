# ProcuraX — Master Development Brief

**Status:** Authoritative implementation brief for the academic/portfolio PoC.  
**Architecture baseline:** ProcuraX PoC Build & Showcase Master Blueprint v3.5 — frozen.  
**Implementation posture:** Build one complete, inspectable end-to-end supplier-disruption decision loop. Do not broaden the project before acceptance evidence supports it.

## 1. Product definition

ProcuraX is an Agentic AI-driven Supply Chain & Procurement Decision Intelligence platform. The flagship PoC is a **governed supplier-disruption risk and mitigation workflow** for a fictional automotive-components manufacturer. The system discovers relevant external signals, estimates supplier risk, quantifies business exposure, compares feasible mitigation options, grounds the recommendation in evidence, applies deterministic policy/RBAC controls, obtains human approval for material action, produces an action packet, records the decision and captures outcomes.

Core loop: **Sense → Predict → Quantify → Simulate → Recommend → Govern → Act → Learn.**

### Fictional demonstration company
- Company: **ApexDrive Components** (fictional; made for the demo, not a real customer).
- Flagship supplier: `SUP-1047` (synthetic supplier entity; Maharashtra; motor components).
- Illustrative event: raw-material/capacity disruption that reduces supply of a critical component.
- Comparison supplier: `SUP-1012` or whichever supplier is present in the generated data and passes checks.
- Do not use a real company's name to imply internal access, partnership, deployment or endorsement.
- Any connection from a real public news article to ApexDrive or a synthetic supplier must be explained as a **scenario assumption** unless supported by an explicit synthetic source-to-entity mapping. Never claim the actual public article is about ApexDrive.

## 2. Audience and roles
- Procurement Manager: investigate suppliers, compare scenarios, submit decisions within policy.
- Supply Chain Planner: understand plant/SKU exposure and supply coverage.
- Executive / Decision Owner: approve material actions within configured thresholds.
- Finance / Risk Reviewer: inspect costs, assumptions, risk, contract evidence and audit trail.
- System Admin: configure data providers, query keywords, role assignments and policy thresholds. Admin actions remain audited.

For local demo mode, seeded demo identities/role-switcher are acceptable if clearly labelled **demo mode** and API authorization checks are still enforced. Do not represent a client-side role switcher alone as production authentication. Keep real auth integration as a documented later step unless already implemented.

## 3. The user-visible outcome
A reviewer must be able to replay one supplier-disruption case and inspect:
1. Original trigger(s), live/public source links, provider and timestamps.
2. Source provenance, relevance/entity-match confidence, deduplication and event classification.
3. ML disruption probability, governed 0–100 score, model version and readable driver contributions — these must remain distinct.
4. Supplier → material → plant → SKU → purchase-order links, inventory runway, exposed quantity and business impact assumptions.
5. At least three feasible mitigation options, preferably four: do nothing, expedite, alternate supplier, hybrid/temporary inventory buffer.
6. Option cost, service impact, lead-time impact, residual risk, constraints and objective value.
7. Evidence-grounded recommendation with citations, or an explicit abstention/escalation if evidence is insufficient.
8. Deterministic policy outcome, decision owner, approval/decline/modification and reason.
9. A traceable action packet and append-only audit log.
10. Outcome fields for expected vs actual values after outcomes are observed.

## 4. Current implementation status (do not assume more than this)
- A starter repository exists with a React/Vite/TypeScript public website + illustrative workspace shell, FastAPI scaffold, SQL schema draft, synthetic data generator, tests, docs and CI configuration.
- The current landing/workspace is a **scaffold**. Mock charts/cards are illustrative and are not evidence of working back-end capability.
- The real-news connector starter is under `integrations/real_data_connectors/`. It is reference/fetcher code, not yet a complete production-shaped ingestion service wired into the API, DB, dashboard or agent.
- Core risk training/evaluation, persistent signal pipeline, end-to-end impact API, optimiser, production RAG, agent state machine, server-side approval workflow and evidence-backed evaluation dashboard must be audited and implemented incrementally.
- Frontend production build/browser verification was previously **not verified** because dependency installation timed out. Recheck locally and report real evidence.
- Inspect current files before editing. Preserve completed behavior. Do not assume this document means a feature already exists.

## 5. Frozen scope

### Must build
- Reproducible synthetic data + data quality checks.
- Data provenance and normalized supplier, SKU/material, plant, purchase order, inventory, performance, contract/policy, signals, risk, scenarios, approval, audit and outcome records.
- Public-signal ingestion with source URL, title, publisher, published/retrieved timestamps, provider, raw payload reference, normalized fields, dedupe and failure handling.
- Entity resolution with confidence, unresolved review queue and explicit fictional-scenario matching.
- Baseline risk model and candidate evaluation with temporal validation, calibration checks where feasible, explainability and leakage guards.
- Governed 0–100 risk scoring separate from model probability.
- Deterministic business impact engine.
- Constraint-aware scenario generation/optimisation.
- RAG over versioned demo contracts/policies; citations and abstention.
- One typed, bounded agent workflow with trigger-dependent hypotheses and one targeted retry maximum.
- A reusable Critic mechanism with different evaluation policies; Critic never authorizes.
- Deterministic Policy Engine/RBAC. Human approval for material actions.
- Append-only audit trail, outcome capture, evaluation/observability and reproducible case replay.
- Professional, responsive, accessible UI with explicit real/synthetic/derived data labels.

### Out of scope for this PoC
- Full ORION multi-vertical platform or general multi-agent swarm.
- SME advertising/market-growth features from other concepts.
- Autonomous high-value purchasing, sending real purchase orders or ERP write-back.
- Real company data claims without permission and a real dataset.
- Production-scale Kubernetes, Kafka, full digital twin or claims of enterprise production readiness.
- Broad logistics/warehouse/dark-store modules unless required to represent the supplier-disruption use case.

## 6. Non-negotiable system boundaries
- **ML service:** outputs disruption probability, model/version and explainability metadata. It does not authorize action.
- **Risk-score mapping:** deterministic, documented, versioned 0–100 score. Never label the ML probability itself as the risk score unless the definitions explicitly match.
- **Impact engine:** all arithmetic from typed, tested functions with formulas and input lineage; never use an LLM to calculate/overwrite financials, quantity, inventory runway or exposure.
- **Optimizer:** solver or deterministic rule engine owns feasibility and objective values; never allow an LLM to invent numeric scenario results.
- **RAG:** retrieves approved content, returns citations and version metadata; it does not make policy.
- **Agent:** orchestrates typed stages and authorized tools; it does not bypass approval.
- **Critic:** judges evidence sufficiency/grounding and gives a specific missing-evidence reason; it is not the Policy Engine.
- **Policy Engine + RBAC:** deterministic server-side authorization and threshold rules.
- **Human:** material action requires an explicit authorized decision; no real external procurement action in the PoC.
- **Outcome service:** stores actual outcomes only after observation and never joins them into prediction-time features for historical examples.

## 7. Agent and Critic workflow
Implement one typed state-machine workflow, not an unrestricted loop:

1. `CASE_CREATED`: create case and correlation/trace ID.
2. `SIGNAL_VALIDATED`: validate provider/source metadata, timestamps and schema; quarantine malformed inputs.
3. `ENTITY_RESOLVED`: match to a fictional supplier/facility/material only through explicit scenario mappings and confidence thresholds. Unresolved means review, not an invented link.
4. `FEATURES_AS_OF`: calculate features at the prediction cutoff; exclude post-cutoff deliveries, post-decision outcomes and injected holdout facts.
5. `RISK_ASSESSED`: compute model probability, governed score, model version and drivers.
6. `HYPOTHESES_ACTIVATED`: activate only hypotheses whose trigger evidence is present. Candidate types can include raw-material shortage, capacity constraint, quality lapse, financial stress, logistics disruption or regulatory restriction. One or more may activate; never require exactly two.
7. `INVESTIGATING`: collect source-linked evidence for each active hypothesis.
8. `CRITIC_GATE_1`: evaluate evidence coverage, reliability, relevance, recency, corroboration, contradictions and confidence.
9. If insufficient, one targeted retry may retrieve/investigate the named evidence gap. It must not perform an open-ended loop.
10. `CRITIC_GATE_2`: if still insufficient, transition to `ABSTAIN_ESCALATE`; do not proceed as if confirmed. If sufficient, continue.
11. `IMPACT_CALCULATED`: compute quantities, inventory runway, impacted SKUs/plants, estimated exposure and assumptions deterministically.
12. `CONSTRAINTS_VALIDATED`: extract policy/contract clauses into a typed schema with provenance, validation and manual-entry fallback. Only validated structures reach the solver.
13. `SCENARIOS_OPTIMIZED`: generate and compare feasible options; record solver/config/model versions and infeasibility reason if none are feasible.
14. `RECOMMENDATION_GROUNDED`: RAG provides evidence-grounded text and citations; it may abstain.
15. `CRITIC_GROUNDING`: evaluate support and consistency; cannot modify numerical truth or authorization.
16. `POLICY_CHECKED`: deterministic Policy Engine verifies user role, action type, spend/cost thresholds, contract rules and required approval.
17. `AWAITING_HUMAN_APPROVAL`: material decision cannot advance without the required role's explicit approval.
18. `ACTION_PACKET_READY`: create a proposal/checklist only; no external PO execution/write-back.
19. `AUDITED`: append actor, timestamps, decisions, references, hashes/versions and reasons.
20. `OUTCOME_PENDING` → `OUTCOME_RECORDED`: later actuals and evaluation labels entered separately.

### Critic evidence policy
Use a shared reusable mechanism with policy-specific evaluation for (a) diagnosis/hypotheses, (b) RAG answer grounding and (c) action-condition review. The Critic response schema should contain at least: `sufficient`, `policy_name`, `findings`, `missing_evidence`, `contradictions`, `source_refs`, `recommended_next_step`, `confidence`, and `retry_allowed`. The retry decision is capped by deterministic state logic, not by the LLM alone.

Store evidence components individually and version weights/configuration. Candidate components: source credibility, freshness/recency, entity/material relevance, cross-source agreement, contradiction penalties, and evidence coverage. A suggested auditable base expression retained by the blueprint is:

`SignalConfidence = SourceCredibility × Recency × Relevance × CrossSourceAgreement`

The actual normalization, weighting, contradiction handling, recency decay and composite-support rubric must be explicit and tested; do not silently invent authoritative weights. Keep the ML probability, evidence support, external-event severity and final governed 0–100 risk score separately visible and in one consistent definition across API, UI and evaluation report.

## 8. Supplier risk model
- Define a single clear prediction target and horizon (e.g., material late delivery/disruption within N days) before evaluation.
- Baseline: Logistic Regression or a simple calibrated tree model.
- Candidate: XGBoost or LightGBM only once baseline and temporal split work. Avoid unnecessary model collection.
- Evaluate with time-aware train/validation/test windows. Do not randomly split time-series/history if it causes leakage.
- Use metrics appropriate to class imbalance: precision, recall, F1, PR-AUC/ROC-AUC where meaningful, confusion matrix, Brier score and calibration plot when probabilities are presented.
- Include baseline/simple heuristic comparison, model card, feature list, limitations and thresholds fixed before final benchmark.
- Explainability with SHAP or a simpler documented feature-contribution method; keep the method reproducible.
- Track feature drift, prediction drift, missingness and performance drift if outcome labels arrive.
- **Flagship injected scenario `SUP-1047` / ApexDrive must remain in the held-out demonstration/time window and must not contaminate model training.** Include an automated regression test that fails if any injected flag is in training rows.
- Actual delivery dates and post-event outcomes are labels, never prediction-time features for that same prediction point.
- Use fixed seed, as-of date, generator version, schema version, and checksums; verify two generation runs are byte-equivalent when inputs are identical.

## 9. Impact and scenario optimisation
- Model relationships: supplier → component/material → SKU → plant/product and linked POs/inventory.
- Expose formulas and assumptions for days of cover/runway, shortage quantity, affected SKU count, plant impact, delay windows and cost exposure.
- The exact monetary figures in the showcase must trace back to typed inputs and formulas. Synthetic assumptions are labeled.
- Create at least three feasible scenarios (target four): do nothing/baseline; expedited shipment; alternate supplier/route or approved allocation; hybrid (expedite + limited buffer/alternative supplier).
- Constraint model should consider, where data exists: supplier capacity, allocation limits, MOQ, lead time, unit cost, expedite cost, contract/approved supplier status, substitution compatibility, plant demand, inventory, target service level, and action thresholds.
- Parse/extract contract/policy values into a validated structured schema. If extraction fails, provide manual-review/manual-entry fallback. Never pass unvalidated LLM-extracted constraints directly to the solver.
- Solver: OR-Tools, PuLP or Pyomo after confirming dependency simplicity; deterministic rules are acceptable in earliest sprint if they prove feasibility and reconcile, but mark optimisation accurately.
- Record `scenario_id`, assumptions, objective value, constraint checks, solver/status, cost breakdown, residual shortage, service impact, risk before/after, infeasibility diagnostics and model/config version.
- If all alternatives are infeasible, explicitly say so and escalate; do not fabricate options.

## 10. Real data, news, market sentiment and provenance

### Provider adapters
Implement provider adapters behind one normalized interface. External provider details must be re-checked against official live documentation at implementation time; rate limits, free-tier quotas, fields and terms can change.
- **GDELT DOC API** — broad public news discovery; no API key for the basic DOC API. It gives article metadata/URLs; ProcuraX must classify event type and relevance itself. Official project/API intro: https://www.gdeltproject.org/data.html and https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- **Marketaux** — market/financial article metadata, identified entities and provider sentiment. Requires the user's own API token. Docs: https://www.marketaux.com/documentation
- **Alpha Vantage `NEWS_SENTIMENT`** — financial/market news with sentiment/topic/ticker metadata, subject to account plan and quota. Requires the user's own API key. Docs: https://www.alphavantage.co/documentation/
- **NewsData.io** — supplementary news feed; requires token; respect free-plan delay/quotas. Docs: https://newsdata.io/documentation
- **SEC EDGAR** — primary company filings/submissions, no API key for public data endpoints. Use a descriptive User-Agent including a valid contact email and respect fair-access guidance. Docs: https://www.sec.gov/edgar/sec-api-documentation
- **Optional future sources:** World Bank commodity-price downloads, FRED API, NOAA weather data, India TRADESTAT, UN Comtrade. Only include a source when it materially supports this use case and its licence/terms are documented.

### Required connector behavior
- API calls occur only on the backend or scheduled/background worker. Never expose tokens to browser JavaScript.
- Use timeouts, retries with bounded exponential backoff, rate-limit-aware handling, provider quota tracking, safe request logging, and a last-success status.
- Handle 401/403, 429, 5xx, timeouts, malformed JSON, empty results and provider outages gracefully.
- Add manual “Fetch now” button gated by role, plus configurable query/topic keywords and date range. Do not schedule rapid polling; use sensible intervals and user-triggered refresh in the PoC.
- Cache/deduplicate results by normalized canonical URL and a title/publisher/time fingerprint. A repeated article from multiple providers may be one evidence item with multiple source observations.
- Preserve raw response files only in ignored local data folder or object storage; normalized database records should include source/provenance. Do not bulk republish full copyrighted articles. Store metadata/snippets and external links unless provider terms clearly permit more.
- Do not make provider failure look like “no risk.” Distinguish `no_results`, `provider_unavailable`, `quota_exceeded`, `partial_success`, and `fetched` states.
- Show `last fetched`, `data freshness`, provider status and count of returned/filtered/deduplicated records.
- No API key is supplied with this brief. User registers their own credentials and enters them into ignored `.env` / local secret store.

### Normalized article/signal schema
At minimum:
`signal_id`, `provider`, `provider_article_id`, `title`, `description_or_snippet`, `canonical_url`, `publisher`, `published_at_utc`, `retrieved_at_utc`, `language`, `search_query`, `entity_name`, `entity_type`, `entity_symbol`, `entity_match_score`, `provider_sentiment_score`, `our_sentiment_label`, `event_type`, `event_severity`, `affected_country_region_port_facility`, `mapped_supplier_id`, `mapping_method`, `mapping_confidence`, `source_credibility`, `recency_score`, `relevance_score`, `cross_source_agreement`, `contradiction_flag`, `evidence_confidence`, `procurement_exposure_match`, `review_status`, `raw_payload_path`, `ingestion_status`, `error_code`, `schema_version`.

Raw/provider sentiment must be distinct from event severity, supplier linkage, evidence confidence and ProcuraX's governed risk score. A negative share-price story is not automatically an operational supply risk. A neutral article about an export restriction can still describe a high-severity threat.

### News event taxonomies
Start with: `supplier_shutdown`, `capacity_reduction`, `raw_material_shortage`, `component_shortage`, `quality_issue`, `financial_distress`, `labor_strike`, `port_congestion`, `shipping_delay`, `export_restriction`, `sanctions`, `natural_disaster`, `weather_disruption`, `cyber_incident`, `regulatory_change`, `commodity_price_shock`, `other`, `unknown`.

### Sentiment and risk separation
- Provider sentiment (where supplied) is recorded unchanged with provider name/model metadata.
- ProcuraX may run a separate configurable text/event classifier on headline/snippet. Persist model version, input fields and output labels.
- Combine event severity, relevance, recency, source reliability and corroboration in the evidence/risk fusion layer; don't make article polarity the sole decision input.
- External public data is an evidence lead. Match it to the fictional business only through explicit scenario rules. Do not infer a relationship just because the article mentions an actual company, region or commodity.
- Add a UI chip for data provenance: `REAL PUBLIC SIGNAL`, `SYNTHETIC OPERATIONS`, `DERIVED ESTIMATE`, `ILLUSTRATIVE`.

## 11. RAG and contract/policy evidence
- Index only owned, licensed, public-domain or synthetic demo documents, with file/version metadata and permitted use.
- Demo contract/policy documents must be explicitly tagged synthetic if fictional.
- Persist document ID/title/version/date, authority type, clause/chunk ID, retrieval timestamp, access role and source location/page.
- Recommendation responses must cite evidence with source links/contract section references; if no adequate result, abstain and request review.
- Test prompt injection embedded in news/articles/documents; retrieved text is untrusted data, never a system instruction.
- Validate document access before retrieval. Do not leak restricted contract chunks through the copilot.
- Run a fixed evaluation set for groundedness, citation correctness, relevance, abstention, access control and unsupported-answer behavior.

## 12. Deterministic policy and approval
- Policy checks must run server-side on every material transition.
- Policy config is versioned and tested: allowed action types, cost/spend thresholds, buyer/approver roles, approved supplier requirement, MOQ/capacity/contract checks and mandatory approval rules.
- Human approval record: `approval_id`, `case_id`, `actor_id`, `role`, `decision`, `reason`, `selected_scenario_id`, `policy_version`, `created_at`, `evidence_refs`, `modified_terms`.
- Allowed decisions: approve, modify, request more evidence, reject, escalate.
- An approval must be bound to a scenario/version. Editing a scenario after approval invalidates approval and requires a new decision.
- The action packet is a proposed action/checklist/export only. No live purchase-order creation or ERP write-back.
- Audit events are append-only at the application level; if database immutability is not implemented, document the limitation and restrict update/delete permissions.

## 13. UI/UX requirements

### Screens
1. **Executive Control Tower** — priority queue ranked by risk × exposure, top exceptions, trend, active/unknown/stale signal count, freshness and drill-down.
2. **Supplier 360** — profile, operational KPIs (OTIF, lead time, quality, capacity), recent signals, evidence links, dependencies and risk drivers.
3. **Impact Map** — supplier → component → SKU → plant, affected quantities, inventory runway and traceable assumptions. Avoid decorative fake geospatial maps if locations are not accurate.
4. **Scenario Studio** — compare 3–4 options across total cost, lead time, service level, residual risk, feasibility and constraints. Keep assumptions inspectable; scenario comparison should be keyboard accessible.
5. **Evidence Panel** — original article title/link, publisher, published/retrieved time, provider, sentiment, event classification, matched entity/confidence, corroborating/contradictory evidence and citations.
6. **Approval Workbench** — recommendation, chosen option, policy checks, required approver, cost threshold, approve/modify/request evidence/reject/escalate, reason and audit preview.
7. **Outcome Review** — expected vs actual KPI form, outcome timing, label and post-event lessons.
8. **Evaluation Dashboard** — model metrics, calibration, confusion matrix, signal quality/freshness, retrieval metrics, agent retry/abstention, solver feasibility, latency/errors/cost and version IDs. Only show values sourced from real run/evaluation records; otherwise mark `not evaluated`.

### Public website / home
- Keep the current refreshed product website as the public landing experience and keep the workspace accessible with a clear “Open workspace / Demo” action.
- Landing page can use aspirational copy, but don't claim customer outcomes, saved money, real-time accuracy or production deployment without evidence.
- Show “Illustrative automotive case study using real public signals and synthetic internal data” where scenario details appear.

### Visual identity
Use `docs/DESIGN_SYSTEM.md` as the source of truth for current Website Refresh v2. In short:
- Light-first editorial SaaS, warm white `#F7F8F5`, white `#FFFFFF`, ink `#151B2C`, secondary text `#657084`, border `#E2E6E8`.
- Dark indigo product panel `#171D37` only for contained visual sections.
- Ocean teal `#0AA995` / deep teal `#087F78` primary action; cyan `#55DCE5` signal/path; violet `#8B7CFF` agent; citron `#D9FA78` rare emphasis; coral `#FF916F` critical; amber `#FFBF69` review.
- Typography: Manrope headings, DM Sans body, DM Mono sparingly for technical metadata, with system fallbacks.
- The neon supply-chain emblem belongs in a contained hero visual / brand moment, not as a repeating background across every app screen.
- Borrow design principles, not exact UI, from Linear/Notion (workspace clarity), Heron AI/Epiminds (agent workflow), Spline/Luma/Active Theory (one restrained memorable visual moment). Do not clone reference sites.
- Use subtle, purposeful motion; respect `prefers-reduced-motion`; avoid constant particles and rainbow gradients.
- Accessible contrast (WCAG AA target), visible focus, meaningful labels, keyboard navigation, semantic headings, status text + icon (never colour only), responsive desktop/tablet/mobile layouts.
- Every table/chart/card has loading, empty, stale, error and success states as appropriate. Charts include units, time window and data-source label.
- Do not animate operational values in a way that implies a live measurement. Mark static demo values illustrative.

## 14. Recommended architecture
- Frontend: React + Vite + TypeScript; keep existing component/project conventions unless there is evidence to change.
- Backend: Python + FastAPI, Pydantic typed schemas, versioned API (`/api/v1`).
- Database: PostgreSQL; use migrations instead of ad hoc schema drift. pgvector for document embeddings when the embedding dimensions/provider are decided.
- Data: raw/public payload references + normalized relational records; generated and processed files in ignored local `data/` folders with manifests/checksums.
- ML: scikit-learn baseline, optional XGBoost/LightGBM candidate, SHAP or a transparent alternative.
- Optimisation: OR-Tools / PuLP / Pyomo only if installed/appropriate; avoid heavy solver complexity before feasible scenario behavior is tested.
- Agent: typed state machine with deterministic state transitions; one shared Critic mechanism under context-specific policies.
- LLM: optional provider adapter with typed response parsing, timeout, budget/cost controls and deterministic/rule-based fallback. No LLM key required for core business calculations.
- Observability: structured logs with case/run/provider/version IDs. OpenTelemetry/Langfuse or light local trace log; don't add costly infrastructure for a one-student PoC.
- Tests: pytest, frontend lint/type/build and ideally Playwright end-to-end when stable.

## 15. API shape
Respect and inspect the existing API contracts before adding endpoints. Preferred `/api/v1` groups:
- `GET /health` — process/dependency health.
- `GET /suppliers`, `GET /suppliers/{supplier_id}` — profile and operational features.
- `GET /signals`, `GET /signals/{signal_id}`, `POST /signals/fetch` — normalized signals/status.
- `GET /cases`, `POST /cases`, `GET /cases/{case_id}`, `POST /cases/{case_id}/run` — case lifecycle/replay.
- `GET /risk/{supplier_id}` or typed case-risk endpoint — model probability, governed score, drivers and versions.
- `GET /impact/{case_id}` — exposure/runway + assumptions.
- `POST /scenarios/optimize` or case-specific equivalent — options, feasibility, objective and solver metadata.
- `POST /copilot/query` — evidence-grounded response with citations/abstention and access scope.
- `GET /approvals`, `POST /approvals/{approval_id}/decision` — role-authorized decisions.
- `POST /outcomes` / `POST /cases/{case_id}/outcome` — post-event actuals.
- `GET /evaluation/runs`, `POST /evaluation/run` — actual evaluation records.
- `GET /providers/status` and `POST /providers/{provider}/fetch` — provider health/quota/freshness; protect fetch actions.

Use typed request/response schemas, pagination/filtering where applicable, consistent error shape, HTTP status codes, validation, correlation IDs and OpenAPI. If a capability is unimplemented, return explicit `501` during scaffold stage or a truthful error, never fake success.

## 16. Database entities (adapt to existing schema; do not duplicate models blindly)
At minimum design or retain tables for:
- `supplier`, `material` / `component`, `sku`, `plant`, `supplier_material`, `supplier_sku_plant_relationship` or equivalent.
- `purchase_order`, `shipment` / `delivery`, `inventory_position`, `supplier_performance_period`.
- `external_signal`, `signal_observation` (provider-specific observation), `signal_entity_match`, `evidence_link`.
- `risk_assessment`, `model_version`, `model_evaluation_run`, `feature_snapshot`/prediction cutoff.
- `business_impact_assessment`, `impact_line_item`.
- `scenario_run`, `scenario_option`, `scenario_constraint_check`.
- `document`, `document_chunk`, `retrieval_evaluation`.
- `case`, `agent_run`, `agent_state_transition`, `critic_evaluation`.
- `policy`, `policy_version`, `approval`, `action_packet`.
- `audit_event`, `outcome_record`, `evaluation_run`, `provider_status`.

Choose UUID or stable string IDs consistently. Add foreign keys, uniqueness, indexes (supplier ID, timestamps, canonical URL/hash, case IDs), UTC timestamps, created/updated metadata and schema migrations. Avoid duplicating article data when only provider observation differs. Do not persist unneeded full copyrighted text.

## 17. Security and privacy
- `.env` is never committed; `.env.example` has placeholders only.
- API tokens stay server-side and are masked in UI/logs. No secrets in screenshots, stack traces, prompts, tests or `VITE_*` variables.
- Provider fetch is protected against abuse/rate exhaustion. Set caps and use allow-listed provider IDs.
- Validate input sizes and URLs; defend against SSRF by avoiding arbitrary user-supplied fetch URLs. Only approved provider URLs or configured feeds are fetched server-side.
- Treat news, HTML, PDF and retrieved text as untrusted; defend against prompt injection and HTML/XSS. Escape/sanitize excerpts and never execute retrieved markup.
- Server-side RBAC and policy gate every protected API and state transition.
- CORS limited to configured frontend origin; use secure cookies/tokens only if proper auth is implemented.
- Avoid logging sensitive text, full API tokens, or full request headers.
- Respect rate limits, provider ToS, robots/website conditions and copyright. Record data licence/source metadata.
- No direct external procurement action. Demo action packet only.

## 18. Testing and evaluation
- Unit tests: feature cutoffs/leakage, risk score mapping, confidence formula, entity matching, deduplication, data quality, inventory runway, exposure formulas, constraints, infeasibility, Critic retry cap, policy permissions and approval state transitions.
- Integration tests: API ↔ database, external provider mocked responses/error conditions, RAG citations/access filters, optimizer to impact input, audit replay.
- Frontend tests: render/loading/error/empty/stale states; role-based action controls; scenario selection; approval validation; source links and provenance badges.
- E2E: clean start → load/replay flagship case → inspect signal → risk → impact → compare options → open citations → request/approve action (using demo role) → view audit/outcome state.
- Provider tests must use recorded fixture payloads, not call live APIs in default CI. Live smoke tests are opt-in and quota-aware.
- Test secret absence with scan/grep and ensure `.env`/raw data are ignored.
- Track model metrics, signal fetch success/latency/age, entity match quality, dedup rate, RAG groundedness/citation accuracy/abstention, solver feasibility rate, agent retry/escalation, policy bypass tests and API error rate.
- Predefine benchmark threshold and test split before final evaluation. If data does not support reliable ML claims, be explicit and focus the showcase on tested workflow/decision traceability.

## 19. Definition of done
Do not call ProcuraX complete until:
- Reproducible data snapshot and source provenance exist.
- Data-quality checks pass; stable IDs and relationships reconcile.
- Baseline/candidate model compared on temporal holdout; model version/drivers shown.
- Injected flagship is excluded from training and proven by test.
- External signal adapter stores normalized records and provenance; provider outages/quotas are handled.
- The UI differentiates real public, synthetic, derived and illustrative data.
- Impact outputs reconcile exactly to inputs/formulas.
- At least three feasible scenarios are compared; constraints pass and objective reconciles.
- RAG citations resolve to authorized sources or the agent abstains.
- Critic retry is capped at one; failure to reach evidence sufficiency escalates.
- The Policy Engine alone authorizes; material action requires appropriate human approval.
- Audit can replay the decision and outcome structure exists.
- Evaluation dashboard is backed by actual runs and labels unmeasured values as `not evaluated`.
- Backend tests, frontend production build, and a repeatable end-to-end demo pass in the target environment.
- README/setup, limitations, provenance and resume/LinkedIn-safe wording are complete.
- Every published metric is labelled measured, backtested, derived estimate or illustrative.

## 20. Required output from coding agent after every task
1. Summary of change and reason.
2. File list changed.
3. Acceptance criteria checked.
4. Exact commands run and PASS/FAIL/NOT VERIFIED outputs.
5. Any logs/metrics/screenshots/artifacts that prove the result.
6. Known defects, assumptions and unverified items.
7. Updated status/next task.

Never claim “done”, “tested”, “live”, “accurate”, “optimized”, “secure” or “deployed” without evidence. Never silently change this frozen architecture. If a meaningful design/architecture change seems necessary, explain evidence, options, trade-offs and request confirmation before changing it.
