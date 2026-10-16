# Test strategy and quality gates

## Unit
- Business impact formulas: runway, units-at-risk × contribution margin × stockout probability, rounding, zero/negative inputs.
- Evidence Critic composite formula: bounds, expected weighted calculation, missing evidence handling.
- Policy engine: threshold boundary, actor role, blocked/approved action, no LLM override.
- Feature transforms: prediction-time boundaries, missingness, numeric ranges.

## Data
- Schema validity, IDs/uniqueness, duplicates, date order, non-negative inventory, valid proportions, provenance metadata.
- Same generator seed/as-of/scale produces same CSV content and checksums under pinned numpy/pandas versions.
- SUP-1047 injected disruption is present in the held-out replay/test window and never in training rows.

## Model
- Temporal split only for time-dependent risk.
- Compare candidate to a simple baseline on PR-AUC/precision/recall/calibration/Brier score.
- Freeze target horizon, cutoffs, thresholds and evaluation protocol before final run.
- Persist data/schema/model/config versions and drivers; evaluate drift later.

## Optimiser
- Capacity/MOQ/contract/lead-time/service constraints; objective calculation reconciliation; infeasibility explanation; sensitivity cases.
- Gate: all solver constraint tests pass.

## RAG / Agent
- Retrieval relevance/recall, citation accuracy, groundedness, abstention correctness, source permission filters.
- Prompt injection in user input and retrieved documents.
- Hypotheses activated only by matching triggers.
- Exactly one targeted follow-up maximum; still insufficient means abstain/escalate.
- Critic cannot modify numerical outputs and cannot authorise an action.

## API / UI / E2E
- Schema validation, auth once implemented, idempotency, error codes, request limits.
- Critical journey UAT at desktop/tablet widths, keyboard focus, loading/empty/error/success states.
- Full flagship case replay with run ID and commit SHA; repeated inputs should produce repeatable deterministic outputs except explicitly nondeterministic/provider-generated text.

## Evidence policy
Report `PASS`, `FAIL` or `NOT VERIFIED`. Store reports/metrics in `artifacts/` but do not commit large raw data/model blobs by default. No benchmark/ROI statement without calculation and baseline documentation.
