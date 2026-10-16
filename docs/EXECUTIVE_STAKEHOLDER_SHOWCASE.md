# ProcuraX — Executive Stakeholder Presentation & Showcase Walkthrough
**Autonomous Decision Intelligence for Sovereign Supply Chain Resilience**

---

## 1. Executive Summary & Value Proposition

**ProcuraX** is an enterprise-grade, governed decision-intelligence platform engineered specifically for tier-1 automotive manufacturing (fictional flagship: **ApexDrive Components**). Unlike generic business intelligence tools or autonomous agent swarms, ProcuraX delivers a single, mathematically verified, human-in-the-loop decision loop for supplier disruptions:

- **Sense & Corroborate:** Real public market signals (GDELT, Marketaux, Alpha Vantage, NewsData.io, SEC EDGAR) corroborated with synthetic enterprise inventory, BOMs, and ERP PO contracts.
- **Calibrated ML Risk:** Proprietary calibrated machine learning (`risk-model-calibrated-v1.0`) with Expected Calibration Error (ECE) tracking and an explicit holdout contamination guard for `SUP-1047`.
- **Deterministic Impact Engine:** 100% mathematical reconciliation of plant runways, safety stock buffer penetration, and revenue-at-risk against SKU unit contribution margins.
- **Solver-Backed Optimization Studio:** MILP-optimized mitigation scenarios evaluating supplier capacity ceilings, MOQs, expedite surcharges, and tooling requalification costs.
- **Governed Human Approval:** 11-step typed state machine, shared Critic with a 1-retry cap, deterministic Policy Engine RBAC spend authorization, and **Proposal-Only Action Packets** sealed with SHA-256 integrity hashes (zero direct live ERP write-backs).

---

## 2. Live Showcase Walkthrough Recording

The video below records the live end-to-end interactive decision intelligence loop and operational surfaces running in the browser:

![ProcuraX Stakeholder Showcase Walkthrough](file:///C:/Users/parth/.gemini/antigravity-ide/brain/7c643446-fc8f-457c-ad5a-e9c89d3b7b47/stakeholder_showcase_1792150893903.webp)

---

## 3. The Governed 8-Stage Decision Loop

| Stage | Operational Objective | Underlying Technology & Separation of Concerns |
|---|---|---|
| **01 SENSE** | Ingest external public signals (news, regulatory filings, logistics indices). | Idempotent PostgreSQL persistence, URL & SHA-256 deduplication, exponential backoff retries, and freshness tiering (`fresh`, `recent`, `stale`, `archived`). |
| **02 DETECT** | Evaluate supplier disruption risk probability and identify degrading suppliers. | Calibrated ML classifier (`risk-model-calibrated-v1.0`), ECE tracking, driver decomposition, and runtime contamination guard quarantining `SUP-1047`. |
| **03 QUANTIFY** | Traverse supply network graph to calculate inventory runway and economic exposure. | Deterministic formulas (`impact-v1.0`), buffer penetration, assembly plant stockout risk (Pune, Chennai, Greater Noida), and SKU unit contribution margin lineage. |
| **04 SIMULATE** | Generate constraint-validated mitigation candidates and sensitivity analysis. | Optimization solver evaluating MOQs, capacity limits, expedite rates, and tooling fees across candidates `SCN-A` through `SCN-D`. |
| **05 RECOMMEND** | Ground mitigation plans in authoritative contractual clauses and corporate policy. | Hybrid RAG copilot with verifiable clause citations (`DOC-MSA-APEX-2025`, `DOC-POL-DUAL-SOURCE`) and honest abstention guarantees (`abstained: true`). |
| **06 GOVERN** | Critic validation, dynamic trigger-dependent hypotheses, and policy spend gating. | Shared Critic with strict 1-retry cap, escalation to human (`ESCALATED_TO_HUMAN`), and deterministic Policy Engine RBAC spend limits (e.g., CPO approval threshold). |
| **07 ACT** | Issue cryptographically sealed Proposal-Only Action Packet. | Action packet generation with `is_proposal_only: True` and SHA-256 hash seal; zero unverified automated ERP/PO write-backs. |
| **08 LEARN** | Record post-decision actual operational outcomes and reconcile impact forecasts. | Post-decision telemetry capture, structured outcome tracking, and append-only audit trail logging with distributed `trace_id` correlation. |

---

## 4. Master Release Quality Gateway (100% Passing)

```
================================================================================
PROCURAX REGRESSION SCORECARD & RELEASE READINESS REPORT
================================================================================
[PASS]   1. Repository Structure             : All required directories and starter files present
[PASS]   2. Python Compilation               : Syntax & bytecode clean
[PASS]   3. Data Integrity & Leakage         : 8 tables validated, SUP-1047 holdout guard active
[PASS]   4. Backend Tests                    : 106 tests passed across 16 test suites (100%)
[PASS]   5. Secret Hygiene                   : Clean scan, zero real credentials committed
[PASS]   6. Showcase Replay                  : All 8 stages (Sense to Learn) passed
[PASS]   7. Frontend Production Build        : TypeScript + Vite production bundle clean
--------------------------------------------------------------------------------
Total Execution Time: 163.56s
OVERALL RESULT: [PASS] -- ALL GATES MET. READY FOR PRODUCTION SHOWCASE.
================================================================================
```

---

## 5. Enterprise Data Provenance & Ethical Boundaries

- **Provenances Distinguish Real vs. Synthetic:** Every data point and UI record is explicitly tagged as `PUBLIC_REAL`, `SYNTHETIC`, `DERIVED`, or `ILLUSTRATIVE`.
- **Zero Hallucinated Numbers:** LLMs are strictly forbidden from generating numerical risk scores, inventory runway days, or spend authorizations. All calculations are executed by deterministic Python and mathematical solvers.
- **Contamination Shield:** Injected failure scenario data for `SUP-1047` degradation window (`period_date >= 2026-07-01`) is mathematically quarantined from model training by automated runtime assertions.
- **SSRF & Security Isolation:** Server-side request forgery shields block all non-whitelisted domains, private RFC1918 subnets, and cloud metadata IPs (`169.254.169.254`). Sliding-window rate limiting prevents API abuse.
