"""Governed 0-100 supplier risk score formulation and explainability drivers.

Implements Blueprint Section 12.2 / Table 24:
RiskScore = w1*f(OTIF trend) + w2*f(lead-time trend) + w3*f(quality trend) + w4*f(capacity util) + w5*(SignalConfidence * Severity)

Important: The governed risk score (0-100) is distinct from the ML model disruption probability P(disruption).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np

# Default weights per Blueprint v3.5 Section 12.2
DEFAULT_WEIGHTS = {
    "otif_trend": 0.25,
    "lead_time_trend": 0.20,
    "quality_trend": 0.20,
    "capacity_utilisation": 0.15,
    "external_signal": 0.20,
}
FORMULA_VERSION = "risk-score-formula-v3.5"


@dataclass
class RiskDriver:
    name: str
    contribution_points: float
    description: str
    direction: str  # "worsening" | "stable" | "improving"


@dataclass
class GovernedRiskScore:
    supplier_id: str
    governed_score: float  # 0 to 100
    risk_level: str  # "Low" | "Medium" | "High" | "Critical"
    ml_probability: float | None  # Distinct P(disruption)
    driver_breakdown: list[RiskDriver]
    top_drivers: list[str]
    formula_version: str
    metadata: dict[str, Any]


def calculate_governed_risk_score(
    supplier_id: str,
    features: dict[str, float],
    ml_probability: float | None = None,
    weights: dict[str, float] | None = None,
) -> GovernedRiskScore:
    """Compute governed 0-100 risk score and explainable driver decomposition."""
    w = weights or DEFAULT_WEIGHTS

    # 1. OTIF deterioration sub-score (0-100): negative trend or low 30d OTIF
    otif_trend = features.get("otif_trend", 0.0)
    otif_30d = features.get("otif_30d", 0.95)
    # If otif_trend is negative (deteriorating) or otif_30d < 0.90
    otif_penalty = max(0.0, -otif_trend * 200.0) + max(0.0, (0.95 - otif_30d) * 120.0)
    otif_subscore = min(100.0, otif_penalty)

    # 2. Lead-time trend sub-score (0-100): positive trend (increasing delays)
    lt_trend = features.get("lead_time_trend", 0.0)
    lt_subscore = min(100.0, max(0.0, lt_trend * 8.0))

    # 3. Quality defect sub-score (0-100): defect rate elevation
    defect_30d = features.get("defect_rate_30d", 0.01)
    defect_trend = features.get("defect_rate_trend", 0.0)
    defect_subscore = min(100.0, (defect_30d * 800.0) + max(0.0, defect_trend * 600.0))

    # 4. Capacity utilization strain (0-100): high utilization (>0.80) = high strain
    cap_util = features.get("capacity_utilisation_30d", 0.70)
    if cap_util > 0.80:
        cap_subscore = min(100.0, 50.0 + (cap_util - 0.80) * 250.0)
    else:
        cap_subscore = max(0.0, cap_util * 50.0)

    # 5. External signal sub-score (0-100): severity (1-10) * confidence (0-1)
    sig_sev = features.get("recent_signal_severity", 0.0)
    sig_conf = features.get("recent_signal_confidence", 0.0)
    sig_subscore = min(100.0, (sig_sev * 10.0) * (sig_conf if sig_conf > 0 else 0.5))

    # Composite weighted 0-100 score
    raw_score = (
        w["otif_trend"] * otif_subscore
        + w["lead_time_trend"] * lt_subscore
        + w["quality_trend"] * defect_subscore
        + w["capacity_utilisation"] * cap_subscore
        + w["external_signal"] * sig_subscore
    )
    final_score = round(float(np.clip(raw_score, 0.0, 100.0)), 1)

    # Risk level classification
    if final_score >= 75.0:
        level = "Critical"
    elif final_score >= 55.0:
        level = "High"
    elif final_score >= 35.0:
        level = "Medium"
    else:
        level = "Low"

    # Driver contributions
    drivers = [
        RiskDriver(
            name="Delivery Reliability (OTIF)",
            contribution_points=round(w["otif_trend"] * otif_subscore, 1),
            description=f"OTIF 30d at {otif_30d*100:.1f}% with trend {otif_trend*100:+.1f}%",
            direction="worsening" if otif_trend < -0.02 else ("improving" if otif_trend > 0.02 else "stable"),
        ),
        RiskDriver(
            name="Lead-Time Stability",
            contribution_points=round(w["lead_time_trend"] * lt_subscore, 1),
            description=f"Lead-time trend {lt_trend:+.1f} days",
            direction="worsening" if lt_trend > 1.5 else "stable",
        ),
        RiskDriver(
            name="Quality Defect Trend",
            contribution_points=round(w["quality_trend"] * defect_subscore, 1),
            description=f"Defect rate at {defect_30d*100:.2f}% (trend {defect_trend*100:+.2f}%)",
            direction="worsening" if defect_trend > 0.005 else "stable",
        ),
        RiskDriver(
            name="Capacity Utilisation",
            contribution_points=round(w["capacity_utilisation"] * cap_subscore, 1),
            description=f"Facility utilization at {cap_util*100:.1f}%",
            direction="worsening" if cap_util >= 0.85 else "stable",
        ),
        RiskDriver(
            name="External Signal Evidence",
            contribution_points=round(w["external_signal"] * sig_subscore, 1),
            description=f"Signal severity {sig_sev:.1f}/10 with confidence {sig_conf:.2f}",
            direction="worsening" if sig_sev >= 5.0 else "stable",
        ),
    ]

    # Rank drivers by contribution
    ranked = sorted(drivers, key=lambda d: d.contribution_points, reverse=True)
    top_drivers = [f"{d.name} ({d.contribution_points} pts)" for d in ranked[:3] if d.contribution_points > 0]

    return GovernedRiskScore(
        supplier_id=supplier_id,
        governed_score=final_score,
        risk_level=level,
        ml_probability=round(ml_probability, 4) if ml_probability is not None else None,
        driver_breakdown=ranked,
        top_drivers=top_drivers or ["All metrics within normal bounds"],
        formula_version=FORMULA_VERSION,
        metadata={
            "weights": w,
            "distinction_note": "Governed score (0-100) measures multidimensional operational risk; ML probability measures binary 30-day disruption likelihood.",
        },
    )
