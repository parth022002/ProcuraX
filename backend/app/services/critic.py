"""Small, deterministic evidence-support utility; not an LLM and not an authorisation engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

WEIGHTS = {
    "coverage": 0.30,
    "source_quality": 0.20,
    "corroboration": 0.20,
    "contradiction_inverse": 0.15,
    "recency": 0.15,
}


@dataclass(frozen=True)
class CriticEvidence:
    coverage: float
    source_quality: float
    corroboration: float
    contradiction: float
    recency: float


def _unit_interval(value: float, name: str) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return value


def composite_support(evidence: CriticEvidence) -> float:
    """CompositeSupport per blueprint Section 12.3.2; high means better-supported."""
    coverage = _unit_interval(evidence.coverage, "coverage")
    source_quality = _unit_interval(evidence.source_quality, "source_quality")
    corroboration = _unit_interval(evidence.corroboration, "corroboration")
    contradiction = _unit_interval(evidence.contradiction, "contradiction")
    recency = _unit_interval(evidence.recency, "recency")
    score = (
        WEIGHTS["coverage"] * coverage
        + WEIGHTS["source_quality"] * source_quality
        + WEIGHTS["corroboration"] * corroboration
        + WEIGHTS["contradiction_inverse"] * (1.0 - contradiction)
        + WEIGHTS["recency"] * recency
    )
    return round(score, 4)


@dataclass
class CriticEvaluationResult:
    """Critic response schema matching Blueprint Section 12.3.2 & MASTER_DEVELOPMENT_BRIEF."""
    sufficient: bool
    policy_name: str
    composite_score: float
    findings: str
    missing_evidence: str | None
    contradictions: float
    source_refs: list[str]
    recommended_next_step: str
    confidence: float
    retry_allowed: bool


def evaluate_case_evidence(
    evidence: CriticEvidence,
    source_refs: list[str] | None = None,
    retries_used: int = 0,
    threshold: float = 0.60,
    force_failure: bool = False,
) -> CriticEvaluationResult:
    """Evaluates multi-source evidence sufficiency deterministically.
    
    Enforces Blueprint rule: Maximum ONE retry allowed before escalating.
    """
    refs = source_refs or []
    if force_failure:
        score = 0.35
    else:
        score = composite_support(evidence)

    sufficient = (score >= threshold) and not force_failure
    retry_allowed = (not sufficient) and (retries_used < 1)

    if sufficient:
        findings = f"Evidence sufficiency verified across {len(refs)} sources with composite support {score:.2f} >= {threshold:.2f}."
        missing = None
        next_step = "Proceed to quantitative impact assessment and scenario generation."
    else:
        findings = f"Insufficient evidence: composite support {score:.2f} is below governing threshold {threshold:.2f}."
        missing = "Corroboration from Tier-2 freight or secondary supplier capacity documents missing."
        if retry_allowed:
            next_step = "Execute one targeted investigation retry against secondary intelligence feeds."
        else:
            next_step = "Escalate to human review; retry limit reached (max 1 retry)."

    return CriticEvaluationResult(
        sufficient=sufficient,
        policy_name="POL-EVIDENCE-SUFFICIENCY-V1",
        composite_score=score,
        findings=findings,
        missing_evidence=missing,
        contradictions=evidence.contradiction,
        source_refs=refs,
        recommended_next_step=next_step,
        confidence=round(score * 0.95, 2),
        retry_allowed=retry_allowed,
    )

