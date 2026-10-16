# ProcuraX Workspace Audit & Remediation Plan

**Audit Date:** 2026-10-15  
**Auditor:** Lead Product & Systems Engineer (Antigravity Agent)  
**Baseline Standard:** ProcuraX v3.5 Master Blueprint & Workspace Redesign Specification  
**Focus Artifacts:** `reference_screenshots/01` to `09`, `frontend/src/`, `backend/app/`  

---

## 1. Executive Summary & Configuration Status

| Area | Observed Status | Evidence / Verification |
|---|---|---|
| **PostgreSQL Database** | **HEALTHY / CONNECTED** | Verified via bounded query `SELECT 1 as alive;` against configured `DATABASE_URL` (PostgreSQL on Neon branch). 60 suppliers, 250 SKUs, 250 inventory snapshots seeded. |
| **FastAPI Backend Services** | **HEALTHY / OPERATIONAL** | 60/60 Pytest suite passing (`pytest backend/tests/ -v`). Process health checks, risk scoring, impact engine, multi-objective Pareto solver, and RAG copilot active. |
| **AI Inference / LLM** | **CONFIGURED & WIRED** | `LLM_PROVIDER=groq`, Model `llama-3.3-70b-versatile`. `GROQ_API_KEY` and `OPENROUTER_API_KEY` configured. Deterministic local rule-based critic engine active as zero-cost fallback. |
| **Signal Adapters** | **CONFIGURED & BOUNDED** | GDELT (no auth needed), Marketaux, Alpha Vantage, NewsData.io, SEC EDGAR configured. `SIGNAL_LIVE_FETCH_ENABLED=False` (safe deterministic offline mock fixtures active by default). |
| **Frontend Production Build** | **PASS** | Vite + TypeScript compiling cleanly (`npm run build` completed in 899ms with 0 errors). |
| **Workspace Visual System** | **DEFECTS IDENTIFIED** | Severe visual and layout defects identified across all 9 screens in `reference_screenshots/` due to missing component classes in `workspace.css`, unstyled form controls, and an API schema mismatch. |

---

## 2. Screenshot-by-Screenshot Diagnostic & Root-Cause Analysis

### Screen 1: Control Tower (`01_control_tower.png`)
* **Observation 1 (Blank Providers Table):** The *External Signal Providers* card rendered headers ("Provider", "Status", "Signal Count", "Last Fetched") but the table body was completely blank.
  * **Root Cause (PROVEN):** Schema key mismatch between frontend and backend. `GET /api/v1/signals/providers` returns a direct JSON array `[{provider: 'GDELT', configured: true, status: 'success', message: '...', last_fetched_at: null}, ...]`. In `ControlTowerView.tsx`, the code expected `provRes.providers`. Because `provRes` was an array, `provRes.providers` evaluated to `undefined`, defaulting to `[]`. Since HTTP was 200, `.catch()` never triggered.
* **Observation 2 (Text Concatenation in Live Feed):** Feed items in *Live Intelligence & Sentiment Feed* rendered as raw unformatted text without card backgrounds, margins, or padding (`GDELTSentiment: -0.6510/14/2026Port congestion and freight delays...`).
  * **Root Cause (PROVEN):** The classes `.signal-feed-list`, `.signal-feed-item`, `.signal-header`, `.signal-provider-tag`, `.sentiment-tag`, `.signal-title`, `.signal-disclaimer`, and `.signal-entities` were missing from `workspace.css`.
* **Observation 3 (Lifecycle Count Contradiction):** Stepper reads `Stage 01 / 07`, but KPI tile below reads `Governed Decision Loop: 8-Stage`.
  * **Root Cause (PROVEN):** Hardcoded string `"8-Stage"` in `ControlTowerView.tsx:258`.
* **Observation 4 (Premature Savings Claim):** Stage 7 badge in stepper displays `€1.9M Saved`.
  * **Root Cause (PROVEN):** Hardcoded string in `Workspace.tsx:30` using Euros instead of INR and claiming realized savings before an outcome has been recorded.

---

### Screen 2: Supplier 360 (`02_supplier_360.png`)
* **Observation 1 (Orphan "A" & Concatenated Profile):** An orphan letter "A" appeared above the supplier name, and supplier metadata rendered as unformatted text (`Supplier ID: SUP-1047Category: Automotive High-Voltage HarnessesPrimary Contract: DOC-MSA-APEX-2025...`).
  * **Root Cause (PROVEN):** `.supplier-avatar-large`, `.supplier-title-group`, and `.supplier-submeta` were unstyled in `workspace.css`. The avatar `<span>` had no dimensions, background, or flex centering.
* **Observation 2 (Risk Metric Contradiction):** Card displays `39.7 MEDIUM RISK`, while top stepper badge displays `86 / 100 Risk`.
  * **Root Cause (PROVEN):** `POST /api/v1/risk/score` computes `governed_risk_score: 39.7` for `SUP-1047`, but `PIPELINE_STAGES` in `Workspace.tsx` hardcoded `badge: '86 / 100 Risk'`.
* **Observation 3 (Driver Concatenation):** Top explainable risk drivers rendered as an unbroken string of text without bar charts, dividers, or badges (`OTIF 30d at 63.8% with trend -10.4%Feature: Delivery Reliability (OTIF) 1450% weight...`).
  * **Root Cause (PROVEN):** Missing `.driver-item`, `.driver-bar`, and `.driver-meta` styles in `workspace.css`.
* **Observation 4 (Unstyled Native Select):** `<select id="supplier-select">` had raw browser styling and no padding.
  * **Root Cause (PROVEN):** Missing `.supplier-dropdown` styles.

---

### Screen 3: Impact Network / Impact Map (`03_impact_map.png`)
* **Observation 1 (Broken BOM Dependency Graph):** The multi-tier supply chain dependency chain rendered as raw unformatted text inside a large blank box (`Tier-1 Supplier ApexDrive ComponentsSUP-1047 · Flagship Sole-SourceDISRUPTED (+14d) ➔ Component Category Wiring & Electrical...`).
  * **Root Cause (PROVEN):** `.network-graph-container`, `.graph-tier`, `.tier-label`, `.graph-node`, `.node-status-tag`, `.graph-arrow`, `.graph-plants-column`, and `.plant-node` were completely absent from `workspace.css`.
* **Observation 2 (Raw Range Slider):** Disruption lead time slider rendered as an unstyled native `<input type="range">` crammed against text.
  * **Root Cause (PROVEN):** Missing slider styling and label spacing.

---

### Screen 4: Scenario Studio (`04_scenario_studio.png`)
* **Observation 1 (Solver Comparison Layout):** Missing clear row alignment for cost, avoided loss, service level, runway gain, and ROI across the 4 candidate scenarios.
* **Observation 2 (Copper Highlight):** Active scenario card needs distinct Forest & Copper treatment (`#E58B45` active border, sage tint).

---

### Screen 5: AI Copilot & Evidence Panel (`05_evidence_panel.png`)
* **Observation 1 (Unstyled Role Selector & Clustered Buttons):** "Acting User Role" select and "Suggested Queries" buttons had raw black outlines, no gap, and overlapped the search input.
  * **Root Cause (PROVEN):** `.prompt-chips-bar`, `.prompt-chip`, `.role-selector-group`, `.copilot-query-box`, and `.copilot-input` were missing from `workspace.css`.

---

### Screen 6: Human Approval Workbench (`06_approvals.png`)
* **Observation 1 (Awkward Lifecycle Stepper):** 11-step typed state progression displayed as raw checkmarks `✓` and text items stacked with large empty space.
  * **Root Cause (PROVEN):** `.stepper-horizontal`, `.stepper-node`, `.stepper-dot`, and `.stepper-label` were missing from `workspace.css`.
* **Observation 2 (Tiny Textarea & Clustered Action Buttons):** Justification textarea was compressed into a corner; decision buttons (`[✓ Approve Mitigation] [✎ Modify Allocations (30/70)] [▤ Request Evidence] [✕ Reject Action]`) had raw black borders.
  * **Root Cause (PROVEN):** `.approval-actions-bar`, `.action-btn`, and `.reason-textarea` lacked proper CSS rules.

---

### Screen 7: Outcome Review (`07_outcome_review.png`)
* **Observation 1 (Outcome State Contradiction):** Top KPI cards displayed achieved metrics (`ACTUAL ON-TIME IN-FULL: 94%`, `ACTUAL SPEND: ₹14.20 Lakhs`, `MITIGATED_SUCCESS`) while right-hand panel stated `"No Outcome Recorded Yet"`.
  * **Root Cause (PROVEN):** `OutcomeReviewView.tsx` rendered hardcoded outcome KPIs unconditionally rather than checking whether an outcome record exists.
* **Observation 2 (Raw Form Controls):** Sliders, number inputs, and textareas were unstyled and cluttered.

---

### Screen 8: Data Sources & Scraper Console (`08_data_sources.png`)
* **Observation 1 (Smashed Vertically Collapsed KPIs):** Metrics rendered with label and value concatenated vertically without spacing (`ACTIVE SIGNALS3`, `STORAGE BACKENDNeon Postgres`, `DEDUPLICATIONSHA-256 Hash`, `SCENARIO TARGETSUP-1047`).
  * **Root Cause (PROVEN):** `DataSourcesView.tsx` used `<div className="metric-box">` and `<span className="metric-label">`, but `.metric-box` did not exist in `workspace.css` (only `.metric-card` was defined). In CSS, `<span>` is inline by default, causing text to run together.
* **Observation 2 (Unstyled Buttons):** `[Refresh]`, `[Fetch News Now]`, and `[🌐 Run Web Scraper]` had raw browser button styling.

---

### Screen 9: Integrations & Database Health (`09_integrations.png`)
* **Observation 1 (Smashed Metrics):** Same symptom as Screen 8 (`LATENCY1126.84 ms`, `SUPPLIERS SEEDED60`, `SKUS LOADED250`).
  * **Root Cause (PROVEN):** Same `.metric-box` absence in `workspace.css`.
* **Observation 2 (Misleading Health Claims):** "All live endpoints responsive" claimed before checks were executed.

---

## 3. Preserved Working Functionality
The following core capabilities are verified working and will be preserved:
1. **FastAPI Backend Services:** 60/60 unit tests pass; all mathematical, statistical, optimization, and RAG routes respond.
2. **PostgreSQL Database:** Schema and seed records intact on Neon branch; bounded queries respond with low latency.
3. **Forest & Copper Brand Palette:** Root tokens `#F7F5F0`, `#FFFFFF`, `#1D2926`, `#64716B`, `#176B55`, `#105642`, `#E58B45`, `#BDE3D2`, `#197653`, `#9B631C`, `#BD3F3F`, `#536F83` already applied; zero blue/cyan residual.
4. **Original Brand Logo:** Glowing 3D emblem (`/procurax-neon-emblem.webp`) untouched.
5. **Tenant Isolation:** Co-branding (*ApexDrive Components*) isolated strictly to operational workspace / Control Tower; public landing page remains purely ProcuraX.

---

## 4. Remediation Plan & Acceptance Gates

### Phase 1: Shared Design System & Component Styling in `workspace.css`
- Implement robust CSS definitions for:
  - `.metric-box` and `.metrics-grid` (fixing Screens 8 & 9 text collision).
  - `.network-graph-container`, `.graph-tier`, `.graph-node`, `.plant-node`, `.graph-arrow` (fixing Screen 3 BOM graph).
  - `.supplier-header-card`, `.supplier-avatar-large`, `.supplier-submeta`, `.risk-score-display`, `.driver-item` (fixing Screen 2).
  - `.signal-feed-item`, `.signal-header`, `.sentiment-tag`, `.entity-tag` (fixing Screen 1 live feed).
  - Modern form controls: `.role-dropdown`, `.supplier-dropdown`, `.copilot-input`, `.reason-textarea`, styled `<input type="range">`, styled buttons (`.action-btn`, `.prompt-chip`).
  - `.stepper-horizontal`, `.stepper-node`, `.stepper-dot` (fixing Screen 6).

### Phase 2: API Contract Normalization & Screen Bug Fixes
- Normalize `fetchSignalProviders()` in `lib/api.ts` so `GET /api/v1/signals/providers` array correctly maps to `SignalProvider[]`, rendering Screen 1 providers table with live status.
- Reconcile risk score display in `Workspace.tsx` and `Supplier360View.tsx` with backend contract.
- Fix Screen 7 *Outcome Review*: show `"Outcome not recorded"` empty state until saved; prevent premature `€1.9M Saved` in stepper (use dynamic state or `"Pending Approval"`).
- Correct Control Tower metric card from `"8-Stage"` to `"7-Stage"`.

### Phase 3: Verification & Evidence
- Run `npm run build` (PASS required).
- Run `pytest backend/tests/ -v` (60/60 PASS required).
- Launch browser subagent to capture high-res screenshots of all 9 screens and confirm all 14 visual defects are eliminated.
