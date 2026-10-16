"""Evidence-grounded RAG copilot engine with citation synthesis and abstention guarantees."""
from __future__ import annotations

from typing import List, Optional

from app.schemas.copilot import (
    Citation,
    CopilotQueryRequest,
    CopilotQueryResponse,
    DocumentMetadata,
)
from app.services.rag_copilot.indexing import ROLE_PERMISSIONS, index
from app.services.rag_copilot.retrieval import execute_iterative_retrieval


class RagCopilotEngine:
    """Evidence-grounded Copilot engine enforcing separation of concerns and auditable citations."""

    def list_authorized_documents(self, user_role: str = "PROCUREMENT_MANAGER") -> List[DocumentMetadata]:
        """List documents viewable by the user's RBAC role."""
        allowed_levels = ROLE_PERMISSIONS.get(user_role.upper(), {"ALL"})
        return [meta for meta in index.metadata_registry if meta.access_level in allowed_levels]

    def answer_query(self, request: CopilotQueryRequest) -> CopilotQueryResponse:
        """
        Produce evidence-grounded recommendation with verbatim citations or explicit abstention.
        """
        retrieval = execute_iterative_retrieval(request.query, user_role=request.user_role)

        # 1. Handle Abstention / Adversarial Attempts
        if retrieval.abstained:
            answer_text = (
                f"ProcuraX Copilot Abstention: {retrieval.abstention_reason}"
            )
            return CopilotQueryResponse(
                query=request.query,
                answer=answer_text,
                citations=[],
                abstained=True,
                abstention_reason=retrieval.abstention_reason,
                retrieval_iterations=retrieval.iterations,
                critic_sufficiency_score=round(retrieval.sufficiency_score, 4),
                user_role_applied=request.user_role,
            )

        # 2. Build Verifiable Citations from Retrieved Chunks
        citations: List[Citation] = []
        answer_parts: List[str] = []

        for chunk in retrieval.chunks:
            # Create quote excerpt (first 500 chars)
            quote = chunk.content[:500].strip()
            if len(chunk.content) > 500:
                quote += "..."

            citations.append(
                Citation(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    version=chunk.version,
                    section=chunk.section,
                    quote_text=quote,
                )
            )

            answer_parts.append(
                f"• Per [{chunk.document_title} — {chunk.section} ({chunk.version})]: {chunk.content}"
            )

        grounded_answer = (
            f"Evidence-grounded recommendation based on {len(citations)} authoritative contract/policy clause(s):\n\n"
            + "\n\n".join(answer_parts)
            + f"\n\n[Critic evidence sufficiency score: {retrieval.sufficiency_score:.2f} across {retrieval.iterations} retrieval cycle(s)]."
        )

        return CopilotQueryResponse(
            query=request.query,
            answer=grounded_answer,
            citations=citations,
            abstained=False,
            abstention_reason=None,
            retrieval_iterations=retrieval.iterations,
            critic_sufficiency_score=round(retrieval.sufficiency_score, 4),
            user_role_applied=request.user_role,
        )


copilot_engine = RagCopilotEngine()
