# ProcuraX Acceptance Test Plan

Use this as a required regression list. A feature is complete only after its acceptance checks pass on the active codebase. Record command output and version/commit in `BUILD_STATUS.md` or the evaluation artifacts.

## A. Repository and setup
- [ ] Clean install on a supported Python and Node version, following README only.
- [ ] `.env.example` contains placeholders only; secrets are not in source, logs, fixtures, UI bundles or Git history.
- [ ] Backend starts with external integrations disabled and works with deterministic fallback.
- [ ] Frontend production build succeeds; inspect landing page and all workspace views at desktop/tablet/mobile breakpoints.
- [ ] Accessibility smoke check: keyboard focus, labels, text contrast, reduced-motion mode and status labels.

## B. Data reproducibility / quality
- [ ] Same seed + as-of date + generator version + scale creates equivalent output hashes.
- [ ] Every entity has stable non-empty ID; foreign-key relationships reconcile.
- [ ] `SUP-1047`/ApexDrive injected flagship records are excluded from training feature/label rows.
- [ ] Future `actual_date`, post-event outcomes and post-decision labels do not leak into prediction-time features.
- [ ] Metadata and checksums are emitted; provenance (`PUBLIC_REAL`, `SYNTHETIC`, `DERIVED`, `ILLUSTRATIVE`) is retained.
- [ ] Invalid/duplicate records are counted and quarantined or reported, not silently dropped.

## C. Providers and signal handling
- [ ] Each connector normalizes fixture responses to common schema.
- [ ] Missing key returns `not_configured` without breaking the whole app.
- [ ] 401/403, 429, 5xx, timeout, malformed JSON, zero results and partial result each map to the right provider status.
- [ ] Tests ensure request limits/retry count are bounded and `Retry-After` is honored where applicable.
- [ ] Canonical duplicate URLs collapse; provider observations remain traceable.
- [ ] API keys are never returned by API, displayed in UI or included in logs/errors.
- [ ] `published_at` and `retrieved_at` are separate UTC fields.
- [ ] Signal evidence UI links to original source and states whether mapping to fictional supplier is synthetic/assumed.
- [ ] Sentiment never acts as the sole disruption label or action trigger.

## D. Risk model
- [ ] Target definition and prediction horizon documented.
- [ ] Temporal split is reproducible and no future features leak into training.
- [ ] Baseline metrics and model metadata are saved; candidate comparison uses same holdout.
- [ ] Risk probability and governed 0–100 risk score are separately exposed and definition is consistent.
- [ ] Drivers link to feature values and model version.
- [ ] Calibration and imbalance-aware metrics reported or marked not evaluated with reason.
- [ ] Risk-score weights/config are versioned; invalid out-of-range score inputs fail validation.

## E. Impact / optimiser
- [ ] Inventory runway/shortage/financial exposure reconcile to fixture inputs and versioned formulas.
- [ ] All reported numbers have units, currency, assumptions and source lineage.
- [ ] At least three mitigation options exist or system clearly states no feasible alternative.
- [ ] Every candidate records feasibility/constraint checks, cost, lead time, service impact, residual risk and objective.
- [ ] Infeasible cases are not silently emitted as feasible.
- [ ] Solver uses only schema-validated policy/contract constraints; extraction failure reaches manual review.

## F. RAG and agent workflow
- [ ] Retrieved policy/contract citations open the correct authorized document/version/section.
- [ ] Unsupported question or insufficient evidence causes abstention, not an invented answer.
- [ ] Prompt-injection text inside external news/document cannot change system instructions or authorization.
- [ ] Trigger-dependent hypotheses activate only when their trigger criteria are met.
- [ ] Agent has at most one targeted retry. If second evidence gate is insufficient, case escalates/abstains.
- [ ] Shared Critic policies are explicit for diagnosis, RAG grounding and action-condition review.
- [ ] Critic cannot change risk numbers, solver objective values, policy config or approval permissions.

## G. Governance / audit
- [ ] Unauthorized user cannot perform protected action even via direct API call.
- [ ] Material action cannot be marked approved without an authorized human approval.
- [ ] Approved scenario version changes invalidate approval.
- [ ] Decisions include actor, role, reason, timestamp, policy version, scenario ID and evidence refs.
- [ ] Audit events are append-only by application design; limitation documented if database owner could mutate rows.
- [ ] Action packet is a proposal only, with no real PO dispatch or external write-back.

## H. UX and evidence transparency
- [ ] Required screens exist: Control Tower, Supplier 360, Impact Map, Scenario Studio, Evidence Panel, Approval Workbench, Outcome Review, Evaluation Dashboard.
- [ ] All unimplemented metrics are labelled `not evaluated` and not fabricated.
- [ ] Real vs synthetic vs derived vs illustrative labels are visible where relevant.
- [ ] Provider failure and stale data are visually distinct from “no risk” / “no results.”
- [ ] Every essential card/table/chart has loading, empty, error and stale handling where applicable.
- [ ] Tables/charts include units, date ranges and provenance.

## I. End-to-end flagship replay
From a clean state:
1. Load deterministic generated operations data and public source fixture/live records.
2. Create/replay the held-out `SUP-1047` case.
3. Inspect signal provenance and event/evidence confidence.
4. Inspect probability, governed risk score, model version and top drivers.
5. Inspect affected SKU/plant/runway and trace impact assumptions.
6. Compare at least three feasible scenarios.
7. Open the citation evidence for the recommendation.
8. Show policy-engine decision and human approval flow.
9. Inspect action packet, audit trail, and outcome-pending state.
10. Open evaluation record and see actual measured values or honest `not evaluated` state.

Target: one repeatable 5-minute demo. Do not call it complete until the full path is rerunnable and evidence is retained.
