"""Iterative retrieval loop with Critic sufficiency scoring and prompt injection defense.
Adopts Section 16.1 agentic RAG: retrieve -> Critic score -> 1 targeted retry -> abstain.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.services.critic import CriticEvidence, composite_support
from app.services.rag_copilot.indexing import DocumentChunk, index

INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"system override",
    r"disregard (all )?policies",
    r"bypass security",
    r"reveal (internal )?(system )?prompt",
    r"output secret tokens",
    r"jailbreak",
]

SUFFICIENCY_THRESHOLD = 0.65


@dataclass
class RetrievalLoopResult:
    """Outcome of the iterative retrieval cycle."""
    chunks: List[DocumentChunk]
    sufficiency_score: float
    iterations: int
    abstained: bool
    abstention_reason: Optional[str]
    is_injection_attempt: bool


def detect_prompt_injection(query: str) -> bool:
    """Identify adversarial injection or jailbreak attempts."""
    query_lower = query.lower()
    return any(re.search(pattern, query_lower) for pattern in INJECTION_PATTERNS)


STOP_WORDS = {
    "what", "is", "the", "and", "or", "for", "in", "to", "of", "a", "an", "does", "which",
    "are", "be", "by", "on", "with", "as", "at", "from", "it", "this", "that", "how", "can"
}


def score_retrieval_sufficiency(
    query: str,
    scored_chunks: List[Tuple[DocumentChunk, float]],
) -> float:
    """Compute Critic sufficiency score using Table 40 / Section 12.3.2 rubric."""
    if not scored_chunks:
        return 0.0

    # Extract meaningful content keywords, ignoring stop words
    all_tokens = set(re.findall(r"\w+", query.lower()))
    content_tokens = {w for w in all_tokens if w not in STOP_WORDS and len(w) > 2}
    if not content_tokens:
        content_tokens = all_tokens

    covered_tokens = set()
    source_quality_sum = 0.0

    for chunk, _ in scored_chunks:
        chunk_tokens = set(re.findall(r"\w+", chunk.content.lower() + " " + chunk.section.lower() + " " + chunk.document_title.lower()))
        covered_tokens.update(content_tokens & chunk_tokens)
        source_quality_sum += 0.95 if chunk.category in {"CONTRACT", "POLICY"} else 0.75

    coverage = len(covered_tokens) / max(1.0, len(content_tokens))

    # If key content words are largely missing (coverage < 40%), evidence is insufficient
    if coverage < 0.40:
        return 0.25

    avg_quality = source_quality_sum / max(1.0, len(scored_chunks))
    corroboration = min(1.0, len(scored_chunks) * 0.35)

    evidence = CriticEvidence(
        coverage=min(1.0, coverage),
        source_quality=min(1.0, avg_quality),
        corroboration=min(1.0, corroboration),
        contradiction=0.0,
        recency=0.95,
    )
    return composite_support(evidence)


def extract_query_gap(query: str, covered_chunks: List[DocumentChunk]) -> str:
    """Identify missing topical keywords to formulate a targeted follow-up query."""
    query_tokens = set(re.findall(r"\w+", query.lower()))
    covered = set()
    for c in covered_chunks:
        covered.update(re.findall(r"\w+", c.content.lower()))
    missing = query_tokens - covered

    # Exclude common stop words
    stop_words = {"what", "is", "the", "and", "or", "for", "in", "to", "of", "a", "an", "does", "which"}
    meaningful_missing = [w for w in missing if w not in stop_words and len(w) > 2]

    if meaningful_missing:
        return f"{query} {' '.join(meaningful_missing)}"
    return f"{query} policy clause agreement terms"


def execute_iterative_retrieval(
    query: str,
    user_role: str = "PROCUREMENT_MANAGER",
) -> RetrievalLoopResult:
    """
    Execute governed iterative retrieval:
    1. Check prompt injection
    2. Retrieve initial top chunks
    3. Critic evaluates sufficiency
    4. If insufficient, retry once with targeted follow-up query
    5. If still insufficient after 1 retry, abstain cleanly
    """
    # 1. Prompt Injection Defense
    if detect_prompt_injection(query):
        return RetrievalLoopResult(
            chunks=[],
            sufficiency_score=0.0,
            iterations=1,
            abstained=True,
            abstention_reason="Adversarial prompt injection attempt detected. Internal procurement governance policies remain strictly authoritative.",
            is_injection_attempt=True,
        )

    # 2. Initial Retrieval (Iteration 1)
    initial_matches = index.search(query, user_role=user_role, top_k=4)
    chunks = [m[0] for m in initial_matches]
    sufficiency = score_retrieval_sufficiency(query, initial_matches)

    if sufficiency >= SUFFICIENCY_THRESHOLD:
        return RetrievalLoopResult(
            chunks=chunks,
            sufficiency_score=sufficiency,
            iterations=1,
            abstained=False,
            abstention_reason=None,
            is_injection_attempt=False,
        )

    # 3. Targeted Retry (Iteration 2 — Cap at exactly 1 retry per Section 16.1)
    gap_query = extract_query_gap(query, chunks)
    second_matches = index.search(gap_query, user_role=user_role, top_k=4)

    # Combine unique chunks from both iterations
    seen_ids = {c.chunk_id for c in chunks}
    for chunk, _ in second_matches:
        if chunk.chunk_id not in seen_ids:
            chunks.append(chunk)
            seen_ids.add(chunk.chunk_id)

    combined_scored = [(c, 1.0) for c in chunks]
    second_sufficiency = score_retrieval_sufficiency(query, combined_scored)

    if second_sufficiency >= SUFFICIENCY_THRESHOLD:
        return RetrievalLoopResult(
            chunks=chunks,
            sufficiency_score=second_sufficiency,
            iterations=2,
            abstained=False,
            abstention_reason=None,
            is_injection_attempt=False,
        )

    # 4. Still insufficient after retry -> Explicit Abstention (no invention/hallucination)
    return RetrievalLoopResult(
        chunks=chunks,
        sufficiency_score=second_sufficiency,
        iterations=2,
        abstained=True,
        abstention_reason="Insufficient grounded evidence in authorized document corpus to support a definitive conclusion without manual review.",
        is_injection_attempt=False,
    )
