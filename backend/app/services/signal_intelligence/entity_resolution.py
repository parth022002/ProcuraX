"""Entity resolution and scenario mapping engine for ProcuraX.

Links real public market signals to synthetic supplier entities using explicit scenario rules
and confidence scoring. Enforces mandatory scenario assumption disclaimers.
"""
from __future__ import annotations

import re
from typing import Any

from app.services.signal_intelligence.schema import NormalizedSignal

SCENARIO_DISCLAIMER = (
    "Scenario assumption: Real public external signal mapped to fictional supplier "
    "for PoC decision replay only. Not an assertion of real-world liability."
)

# Known scenario aliases and target mappings
SUPPLIER_RULES = [
    {
        "supplier_id": "SUP-1047",
        "canonical_name": "ApexDrive Components",
        "patterns": [r"apexdrive", r"apex\s*drive"],
        "materials": ["bldc motor", "magnetic coil", "copper", "stator"],
        "region": "Maharashtra",
        "category": "Motor components",
    },
    {
        "supplier_id": "SUP-1012",
        "canonical_name": "ElectroMotion Systems",
        "patterns": [r"electromotion", r"electro\s*motion"],
        "materials": ["electric drive", "inverter", "power module"],
        "region": "Gujarat",
        "category": "Motor components",
    },
]

# Material & commodity triggers
COMMODITY_RULES = {
    "copper": {"material": "high-grade copper wire", "severity_boost": 0.25, "event": "raw_material_shortage"},
    "semiconductor": {"material": "microcontrollers", "severity_boost": 0.20, "event": "capacity_constraint"},
    "port congestion": {"material": "logistics corridor", "severity_boost": 0.15, "event": "port_delay"},
    "refinery maintenance": {"material": "smelted metal", "severity_boost": 0.20, "event": "raw_material_shortage"},
}


def resolve_signal_entity(
    signal: NormalizedSignal,
    allow_scenario_assumptions: bool = True,
) -> NormalizedSignal:
    """Analyze signal title, snippet, and entity fields to map to a supplier entity."""
    text = f"{signal.title or ''} {signal.description_or_snippet or ''} {signal.entity_name or ''}".lower()

    best_match: dict[str, Any] | None = None
    highest_confidence = 0.0
    match_method = "none"

    # 1. Direct name/pattern match
    for rule in SUPPLIER_RULES:
        for pat in rule["patterns"]:
            if re.search(pat, text):
                best_match = rule
                highest_confidence = 0.92
                match_method = "direct_entity_name"
                break
        if best_match:
            break

    # 2. Material + Region / Scenario mapping (Flagship scenario rule)
    if not best_match and allow_scenario_assumptions:
        for rule in SUPPLIER_RULES:
            material_hit = any(mat in text for mat in rule["materials"])
            region_hit = rule["region"].lower() in text or "west" in text or "india" in text
            if material_hit and region_hit:
                best_match = rule
                highest_confidence = 0.78
                match_method = "scenario_assumption"
                break
            elif material_hit:
                best_match = rule
                highest_confidence = 0.65
                match_method = "scenario_assumption"
                break

    if best_match:
        signal.mapped_supplier_id = best_match["supplier_id"]
        signal.mapping_method = match_method
        signal.mapping_confidence = round(highest_confidence, 2)
        signal.entity_name = signal.entity_name or best_match["canonical_name"]
        signal.scenario_disclaimer = SCENARIO_DISCLAIMER

    # Event classification and severity calculation
    event_type = signal.event_type
    severity = signal.event_severity

    for term, c_meta in COMMODITY_RULES.items():
        if term in text:
            if event_type == "general_news":
                event_type = c_meta["event"]
            severity = min(1.0, max(severity, 0.50 + c_meta["severity_boost"]))

    signal.event_type = event_type
    signal.event_severity = round(severity, 2)
    # Evidence confidence is a function of source credibility and mapping confidence
    signal.evidence_confidence = round(signal.source_credibility * (signal.mapping_confidence if signal.mapping_confidence > 0 else 0.5), 2)

    return signal
