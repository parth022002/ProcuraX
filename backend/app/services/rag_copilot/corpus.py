"""Authoritative Document Corpus for ProcuraX RAG Copilot.
Contains synthetic and licensed agreements, internal policies, and signal digests.
All documents include explicit IDs, versions, effective dates, and RBAC access tags.
"""
from __future__ import annotations

from typing import Dict, List

RAW_DOCUMENTS: List[Dict] = [
    {
        "document_id": "DOC-MSA-APEX-2025",
        "title": "Master Supply Agreement — ApexDrive Components Pvt. Ltd.",
        "version": "v2.1",
        "effective_date": "2025-01-01",
        "access_level": "PROCUREMENT_MANAGER",
        "category": "CONTRACT",
        "sections": [
            {
                "section": "Section 4.1 & 4.2 — Order Multiples & MOQ",
                "content": (
                    "Orders for BLDC motor components, housings, and sub-assemblies must be placed in standard batch multiples. "
                    "The agreed Minimum Order Quantity (MOQ) is 500 units per purchase order. ApexDrive guarantees a monthly "
                    "manufacturing capacity ceiling of 45,000 units for NovaHome product families under standard operational conditions."
                ),
            },
            {
                "section": "Section 5.3 — Delivery Lead Times & Expedite Terms",
                "content": (
                    "Contractual standard delivery lead time is fourteen (14) calendar days from purchase order acknowledgement. "
                    "In the event of urgent production requirements, NovaHome may trigger expedited delivery terms compressing lead time "
                    "to four (4) business days. Expedited shipments incur an agreed premium surcharge of thirty-five percent (35%) above "
                    "the base unit purchase price of ₹2,850 per component."
                ),
            },
            {
                "section": "Section 8.2 — Alternate Sourcing & Non-Exclusivity",
                "content": (
                    "This Agreement is strictly non-exclusive. NovaHome retains the unilateral contractual right to engage alternate "
                    "or secondary qualified suppliers, including ElectroMotion Systems India Pvt. Ltd., if ApexDrive faces operational, "
                    "labor, or material shortages threatening assembly line continuity at NovaHome manufacturing plants."
                ),
            },
            {
                "section": "Section 12.1 — Delay Penalties & Liquidated Damages",
                "content": (
                    "Any unexcused delivery delay exceeding three (3) business days past the confirmed promised date shall incur a delay "
                    "penalty of ₹25,000 per business day, deducted directly from outstanding accounts payable."
                ),
            },
        ],
    },
    {
        "document_id": "DOC-POL-DUAL-SOURCE",
        "title": "NovaHome Strategic Dual-Sourcing & Vendor Allocation Policy",
        "version": "v2026.1",
        "effective_date": "2026-01-15",
        "access_level": "PROCUREMENT_MANAGER",
        "category": "POLICY",
        "sections": [
            {
                "section": "Section 3.2 — Volume Allocation Ratios",
                "content": (
                    "For all Class-A critical sub-assemblies (criticality rating >= 4), procurement teams must maintain qualified "
                    "secondary sources. In active mitigation events, secondary suppliers must receive a minimum allocation of thirty percent "
                    "(30%) of baseline demand to ensure hot-standby production readiness and operational viability."
                ),
            },
            {
                "section": "Section 4.1 — Alternate Vendor Qualification & Tooling",
                "content": (
                    "Secondary suppliers must possess verified Production Part Approval Process (PPAP) Level 3 sign-off. When activating "
                    "a standby vendor, one-time tooling recalibration and jig setup charges must be budgeted and pre-approved by the Category Director."
                ),
            },
        ],
    },
    {
        "document_id": "DOC-POL-GOV-2026",
        "title": "NovaHome Procurement Delegation of Authority & Governance Matrix",
        "version": "v2026.2",
        "effective_date": "2026-02-01",
        "access_level": "PROCUREMENT_MANAGER",
        "category": "POLICY",
        "sections": [
            {
                "section": "Section 2.1 — Financial Thresholds for Mitigation Approval",
                "content": (
                    "Mitigation decisions involving total expenditure up to ₹10,00,000 (10 Lakhs INR) may be approved by the designated "
                    "Supply Chain Planner or Procurement Manager. Any mitigation action, expedite budget, or dual-sourcing re-allocation "
                    "exceeding ₹10,00,000 requires explicit authorization by the Chief Procurement Officer (CPO) or Category Director."
                ),
            },
        ],
    },
    {
        "document_id": "DOC-POL-CPO-RESERVE",
        "title": "Executive Strategic Contingency Reserve Policy (CONFIDENTIAL)",
        "version": "v2026.1",
        "effective_date": "2026-02-01",
        "access_level": "CPO",
        "category": "POLICY",
        "sections": [
            {
                "section": "Section 6.3 — Executive Strategic Reserve & CPO Discretion",
                "content": (
                    "CONFIDENTIAL / CPO ONLY: The Chief Procurement Officer maintains an emergency strategic contingency reserve of "
                    "₹5.0 Crore for unforecasted geopolitical or multi-tier component disruption. Discretionary release of contingency funds "
                    "requires joint sign-off with the Chief Financial Officer and board audit notification."
                ),
            },
        ],
    },
    {
        "document_id": "DOC-MSA-ELECTRO-2025",
        "title": "Dual-Sourcing Framework Agreement — ElectroMotion Systems India Pvt. Ltd.",
        "version": "v1.0",
        "effective_date": "2025-03-10",
        "access_level": "PROCUREMENT_MANAGER",
        "category": "CONTRACT",
        "sections": [
            {
                "section": "Section 2.2 — Capacity, MOQ & Tooling Terms",
                "content": (
                    "ElectroMotion Systems guarantees secondary standby capacity of up to 50,000 units monthly for motor component assemblies. "
                    "Contractual Minimum Order Quantity (MOQ) is 1,000 units. Standard delivery lead time is ten (10) calendar days; expedited "
                    "lead time is three (3) days with a twenty-five percent (25%) expedite fee. Contracting unit price is ₹2,950 per unit, and "
                    "line activation requires a one-time tooling recalibration payment of ₹1,20,000."
                ),
            },
        ],
    },
    {
        "document_id": "DOC-SIG-MARKET-2026",
        "title": "External Market Signal Intelligence Digest — Maharashtra Regional Shortage",
        "version": "v1.0",
        "effective_date": "2026-07-05",
        "access_level": "ALL",
        "category": "SIGNAL_DIGEST",
        "sections": [
            {
                "section": "Section 1 — Rare Earth & Magnetic Material Shortage Signal",
                "content": (
                    "PUBLIC REAL / SCENARIO ASSUMPTION: Independent trade filings and logistics telemetry report acute regional "
                    "shortages of specialized neodymium magnetic materials in Pune/Pimpri-Chinchwad manufacturing corridors. "
                    "Affected motor component tiers face potential assembly slowdowns of 10 to 18 days unless alternate raw stock is expedited."
                ),
            },
        ],
    },
]
