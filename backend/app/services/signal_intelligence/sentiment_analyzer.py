"""Domain-Specific Market Sentiment & Disruption Velocity Analysis Algorithms.

Implements deterministic quantitative NLP & market sentiment metrics:
1. Supply-Chain Domain Lexicon Sentiment Scorer (Polarities & Compound Score)
2. Disruption Velocity (rate of sentiment decay dS/dt) & Volatility Index
3. Multi-source Entity Stress Aggregator (0 to 100 governed scale)
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, List


# Supply-Chain & Automotive domain lexicon weights (-4.0 to +4.0 scale)
DOMAIN_SENTIMENT_LEXICON: dict[str, float] = {
    # Severe disruption terms
    "strike": -3.5,
    "lockout": -3.2,
    "demurrage": -3.0,
    "insolvency": -3.8,
    "bankruptcy": -4.0,
    "embargo": -3.6,
    "blockade": -3.5,
    "stoppage": -3.4,
    "shortage": -2.8,
    "congestion": -2.6,
    "quarantine": -2.5,
    "force majeure": -3.8,
    "bottleneck": -2.4,
    "default": -3.2,
    "delay": -2.0,
    "delayed": -2.0,
    "halt": -2.7,
    "halted": -2.7,
    "recall": -3.1,
    "downtime": -2.9,
    "penalty": -2.2,
    "breach": -3.0,
    "violation": -2.5,
    "deficit": -2.3,
    "curtailment": -2.4,
    "crisis": -3.0,
    "layoff": -2.5,
    "catastrophic": -3.8,
    
    # Moderate disruption terms
    "drop": -1.5,
    "decline": -1.6,
    "slump": -2.0,
    "tariff": -1.8,
    "sanction": -2.6,
    "dispute": -1.7,
    "risk": -1.2,
    "warning": -1.5,
    "friction": -1.3,
    "vulnerable": -1.8,
    "exposure": -1.4,
    
    # Positive resilience & resolution terms
    "settled": 2.6,
    "agreement": 2.4,
    "resolved": 2.8,
    "recovery": 2.7,
    "surplus": 2.2,
    "dual-source": 2.5,
    "dual-sourcing": 2.6,
    "restocked": 2.3,
    "expedited": 2.1,
    "cleared": 2.4,
    "normalized": 2.5,
    "approved": 2.0,
    "stable": 1.8,
    "mitigated": 2.5,
    "growth": 1.9,
    "expanded": 1.7,
    "reopened": 2.4,
    "operational": 2.0,
    "on-time": 2.3,
    "certified": 1.8,
}


@dataclass
class SentimentAnalysisResult:
    text: str
    compound_score: float  # -1.0 (extreme panic) to +1.0 (strong resilience)
    positive_score: float
    neutral_score: float
    negative_score: float
    detected_keywords: list[str]
    classification: str    # "HIGH_RISK", "MODERATE_RISK", "NEUTRAL", "POSITIVE_RESILIENCE"


@dataclass
class DisruptionVelocityMetrics:
    entity_name: str
    current_sentiment: float
    previous_sentiment: float
    velocity_per_day: float       # dS/dt
    acceleration: float           # d2S/dt2
    volatility_14d: float         # Rolling std
    market_stress_index: float    # 0 to 100 governed scale
    early_warning_tier: str       # "NORMAL", "WATCH", "ELEVATED", "CRITICAL"
    summary_insight: str


class DomainSentimentAnalyzer:
    """Quantitative Rule-Based Sentiment Analyzer tuned for Supply Chains."""

    def __init__(self, lexicon: dict[str, float] | None = None):
        self.lexicon = lexicon or DOMAIN_SENTIMENT_LEXICON

    def analyze_text(self, text: str) -> SentimentAnalysisResult:
        """Score text polarity using domain-weighted token matching."""
        if not text or not text.strip():
            return SentimentAnalysisResult(
                text="",
                compound_score=0.0,
                positive_score=0.0,
                neutral_score=1.0,
                negative_score=0.0,
                detected_keywords=[],
                classification="NEUTRAL",
            )

        clean_text = text.lower()
        matched_tokens: list[str] = []
        scores: list[float] = []

        # Check multi-word keys first
        for phrase, weight in self.lexicon.items():
            if " " in phrase and phrase in clean_text:
                matched_tokens.append(phrase)
                scores.append(weight)

        # Tokenize single words
        words = re.findall(r"\b[a-z\-]+\b", clean_text)
        for word in words:
            if word in self.lexicon and " " not in word:
                matched_tokens.append(word)
                scores.append(self.lexicon[word])

        if not scores:
            return SentimentAnalysisResult(
                text=text[:120],
                compound_score=0.0,
                positive_score=0.0,
                neutral_score=1.0,
                negative_score=0.0,
                detected_keywords=[],
                classification="NEUTRAL",
            )

        pos_sum = sum(s for s in scores if s > 0)
        neg_sum = abs(sum(s for s in scores if s < 0))
        total_valence = pos_sum + neg_sum

        # Normalized compound score using hyperbolic tangent mapping
        raw_sum = sum(scores)
        compound = math.tanh(raw_sum / 5.0)

        pos_ratio = (pos_sum / total_valence) if total_valence > 0 else 0.0
        neg_ratio = (neg_sum / total_valence) if total_valence > 0 else 0.0
        neutral_ratio = max(0.0, 1.0 - (len(scores) / max(len(words), 1)))

        # Normalize ratios
        total_ratio = pos_ratio + neg_ratio + neutral_ratio
        if total_ratio > 0:
            pos_ratio /= total_ratio
            neg_ratio /= total_ratio
            neutral_ratio /= total_ratio

        if compound <= -0.35:
            classification = "HIGH_RISK"
        elif compound < -0.08:
            classification = "MODERATE_RISK"
        elif compound > 0.25:
            classification = "POSITIVE_RESILIENCE"
        else:
            classification = "NEUTRAL"

        return SentimentAnalysisResult(
            text=text[:120],
            compound_score=round(compound, 3),
            positive_score=round(pos_ratio, 3),
            neutral_score=round(neutral_ratio, 3),
            negative_score=round(neg_ratio, 3),
            detected_keywords=list(set(matched_tokens)),
            classification=classification,
        )


class DisruptionVelocityCalculator:
    """Calculates temporal rate of sentiment decay and market panic velocity."""

    @staticmethod
    def calculate_velocity(
        entity_name: str,
        sentiment_history: list[float],
        time_delta_days: float = 7.0,
    ) -> DisruptionVelocityMetrics:
        """Compute dS/dt, rolling volatility, and 0-100 market stress index."""
        if not sentiment_history:
            return DisruptionVelocityMetrics(
                entity_name=entity_name,
                current_sentiment=0.0,
                previous_sentiment=0.0,
                velocity_per_day=0.0,
                acceleration=0.0,
                volatility_14d=0.0,
                market_stress_index=30.0,
                early_warning_tier="NORMAL",
                summary_insight="Insufficient history; baseline stress assigned.",
            )

        if len(sentiment_history) == 1:
            curr = sentiment_history[0]
            stress = max(0.0, min(100.0, 50.0 - (curr * 50.0)))
            return DisruptionVelocityMetrics(
                entity_name=entity_name,
                current_sentiment=round(curr, 3),
                previous_sentiment=round(curr, 3),
                velocity_per_day=0.0,
                acceleration=0.0,
                volatility_14d=0.0,
                market_stress_index=round(stress, 1),
                early_warning_tier="NORMAL" if stress < 60 else "WATCH",
                summary_insight=f"Single observation: sentiment {curr:.2f}.",
            )

        curr = sentiment_history[-1]
        prev = sentiment_history[-2]
        delta_days = max(1.0, time_delta_days)

        # 1. Velocity (1st derivative)
        velocity = (curr - prev) / delta_days

        # 2. Acceleration (2nd derivative if 3+ data points)
        if len(sentiment_history) >= 3:
            prev_prev = sentiment_history[-3]
            prev_velocity = (prev - prev_prev) / delta_days
            acceleration = (velocity - prev_velocity) / delta_days
        else:
            acceleration = 0.0

        # 3. Volatility (Sample Standard Deviation)
        mean_s = sum(sentiment_history) / len(sentiment_history)
        variance = sum((x - mean_s) ** 2 for x in sentiment_history) / max(len(sentiment_history) - 1, 1)
        volatility = math.sqrt(variance)

        # 4. Governed Market Stress Index (0-100)
        # Base stress from negative sentiment + penalty for negative velocity + volatility penalty
        sentiment_penalty = max(0.0, -curr * 50.0)  # Up to 50 pts
        velocity_penalty = max(0.0, -velocity * 120.0)  # Up to 30 pts for rapid drop
        volatility_penalty = min(20.0, volatility * 40.0)  # Up to 20 pts
        stress_score = min(100.0, round(sentiment_penalty + velocity_penalty + volatility_penalty, 1))

        # 5. Early warning classification
        if stress_score >= 80.0 or (velocity < -0.15 and curr < -0.40):
            tier = "CRITICAL"
            insight = f"Critical sentiment collapse (velocity: {velocity:.2f}/day). Disruption imminent."
        elif stress_score >= 60.0 or velocity < -0.08:
            tier = "ELEVATED"
            insight = f"Rapid sentiment deterioration detected. Pre-warning threshold breached."
        elif stress_score >= 40.0:
            tier = "WATCH"
            insight = f"Mild sentiment friction noted. Monitor upcoming public news cycles."
        else:
            tier = "NORMAL"
            insight = f"Market sentiment stable across external information channels."

        return DisruptionVelocityMetrics(
            entity_name=entity_name,
            current_sentiment=round(curr, 3),
            previous_sentiment=round(prev, 3),
            velocity_per_day=round(velocity, 4),
            acceleration=round(acceleration, 4),
            volatility_14d=round(volatility, 3),
            market_stress_index=stress_score,
            early_warning_tier=tier,
            summary_insight=insight,
        )
