# AGENTS.md — ProcuraX Durable Coding-Agent Instructions

## Required reading / source of truth
- Read `PROJECT.md`, `MASTER_CODING_AGENT_PROMPT.md`, and relevant `docs/` before editing.
- The frozen `reference/ProcuraX_PoC_Build_and_Showcase_Master_Blueprint_v3_5.docx` controls the project boundary. `docs/MASTER_DEVELOPMENT_BRIEF.md` is the operational summary.
- If an implementation choice conflicts with v3.5, stop, explain the conflict and request confirmation rather than silently changing architecture.

## Workflow
- Start with repository inspection; never blindly rewrite existing files.
- Work one explicitly approved sprint at a time. Report and wait before moving to the next major sprint.
- Before editing state: goal, files affected, acceptance criteria and risks. After editing: list files, exact commands and test results.
- Update `docs/BUILD_STATUS.md`, `docs/IMPLEMENTATION_PLAN.md`, API docs and `docs/DECISIONS.md` whenever status/architecture changes.
- Mark each check PASS, FAIL or NOT VERIFIED based on actual results only.

## Frozen product scope
One governed supplier-disruption decision loop for fictional ApexDrive Components, with real public external signals and synthetic internal operation data. No generic BI, marketing analytics, multi-agent swarm, autonomous purchasing or live ERP write-back.

## Separation of concerns
- ML predicts; governed risk mapper maps to a 0–100 score; deterministic impact service calculates business figures; solver computes feasibility/objective; RAG retrieves/cites; agent orchestrates; Critic evaluates evidence; Policy Engine/RBAC authorizes; human approves material action; audit/outcome services record results.
- These concepts may not be conflated or delegated to LLM-generated numerical text.
- Hypotheses activate only when triggers support them. One targeted investigation retry maximum. If still insufficient, abstain/escalate.
- Contract constraints must pass schema validation/manual-review fallback before solver use.
- Injected `SUP-1047` / ApexDrive flagship must never enter training rows; add a failing test for contamination.

## Data and truthfulness
- Distinguish `PUBLIC_REAL`, `SYNTHETIC`, `DERIVED`, and `ILLUSTRATIVE` in records and UI.
- Never assert an external real event affects fictional ApexDrive unless a declared scenario mapping supports the assumption and the UI labels it accordingly.
- Never fabricate API results, test results, accuracy, ROI or customer claims.
- Show real external source links and separate published time/retrieved time. Respect provider terms, fair access, quotas and copyright.

## Security
- Never place real credentials in source, docs, prompts, test fixtures, logs or browser bundles. `.env.example` contains placeholders only.
- Validate inputs; constrain external fetchers to approved providers; never fetch arbitrary user-provided URLs server-side.
- Enforce RBAC and policy on the server, not just in UI.
- Treat retrieved content as untrusted; test prompt injection and XSS.
- Do not run destructive commands or modify production resources without explicit permission.

## Code quality
- Prefer minimal, typed, testable changes and existing repository conventions.
- Avoid unnecessary dependencies/infrastructure. Do not add Kafka/Kubernetes/extra agents without an evidence-backed requirement.
- All API failures, unavailable providers, empty states and unimplemented features must be explicit.
- CI must use mocks/fixtures by default; live external requests must be opt-in.
- Check responsive UI and reduced-motion support. Dashboard statuses cannot rely on colour alone.

## Completion report
Always report: changed files; behavior and reason; acceptance criteria; commands run; exact PASS/FAIL/NOT VERIFIED results; artifact evidence; decisions/assumptions; remaining risks; and one suggested next task.
