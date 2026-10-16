# User journeys and navigation

## Primary journey — supplier disruption case
1. **Sign in / select workspace (future auth integration).** The user enters the ProcuraX control tower with a role and permission scope.
2. **View Executive Control Tower.** Review prioritised risk × impact queue and select a case.
3. **Open Supplier 360.** Inspect risk probability/score, drivers, OTIF, lead-time, quality, capacity, open POs and dependency links.
4. **Investigate cause and evidence.** Signal/trigger activates only applicable hypotheses; system retrieves internal records and permitted external evidence. Critic records sufficiency and any gap.
5. **View Impact Map.** Trace supplier → material → plant → SKU, runway, exposure, formulas and assumptions.
6. **Open Scenario Studio.** Compare do-nothing, alternate-supplier, expedite/inventory and hybrid options. Show feasibility, cost, service impact, risk and sensitivity.
7. **Review recommendation.** RAG panel lists source citation, document effective date, provenance, clause text, confidence and abstention status.
8. **Approval Workbench.** Show action packet, exposure threshold, role required, policy check and audit preview. User can approve, modify, request evidence, reject or escalate.
9. **Prepare/dispatch permitted action.** PoC defaults to mock/structured action packets unless an explicitly approved integration exists. No autonomous high-value purchasing.
10. **Outcome Review.** Enter/ingest observed result after the decision, compare actual vs expected and attach a learning label separately from training-time features.
11. **Evaluation Dashboard.** Inspect model/RAG/agent/system/business run evidence and reproduce the case by run ID.

## Alternate and failure journeys
- No matching supplier for signal → place in unresolved queue; request manual entity mapping; do not assign a supplier score.
- Low-quality or stale source → lower source confidence or discard with reason; external signal alone cannot be ground truth.
- One hypothesis activated → evaluate that hypothesis; do not invent a second one just to populate UI.
- Critic says evidence insufficient → one targeted follow-up with a specific gap; if still insufficient, abstain and escalate to a human.
- RAG has no authoritative evidence → show abstention and sources searched; do not fabricate citations.
- Constraint extraction ambiguous → require validated manual entry before optimisation; do not guess solver inputs.
- Optimiser infeasible → report violated constraints/reason and escalation path; do not present an invalid solution.
- Policy blocks action → show reason and permitted next step; never let LLM text override it.
- External API/rate limit failure → record the failure; deterministic fixture/fallback may be used only with a clear “fallback/synthetic” label.
- Data-quality gate fails → stop the dependent model/impact stage or mark output provisional; display the issue.
- Duplicate approval request → use idempotency key / state check to avoid a second dispatch.

## Screen inventory
1. Executive Control Tower — risk × exposure queue, alerts and trend.
2. Supplier 360 — performance/risk/dependencies.
3. Impact Map — affected SKU/plant, runway, exposure.
4. Scenario Studio — 3–4 options, costs, service, capacity, risk, sensitivity.
5. Evidence Panel — clauses, provenance, timestamps and citations.
6. Approval Workbench — action, policy, decision choices and audit preview.
7. Outcome Review — expected vs actual KPI and label.
8. Evaluation Dashboard — quality metrics, run/model versions and limitations.
