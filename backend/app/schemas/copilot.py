"""Pydantic schemas for Sprint 6: RAG Copilot, Evidence Grounding, and Citations."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Verifiable citation linking a statement directly to an authoritative document clause."""
    chunk_id: str
    document_id: str
    document_title: str
    version: str
    section: str
    quote_text: str


class DocumentMetadata(BaseModel):
    """Metadata for an ingested governance, contract, or signal document."""
    document_id: str
    title: str
    version: str
    effective_date: str
    access_level: str  # "ALL", "PROCUREMENT_MANAGER", "CPO"
    category: str  # "CONTRACT", "POLICY", "SIGNAL_DIGEST"
    total_chunks: int


class CopilotQueryRequest(BaseModel):
    """Request payload for RAG copilot investigation."""
    query: str = Field(..., min_length=3, description="Natural language procurement question or investigation prompt")
    user_role: str = Field("PROCUREMENT_MANAGER", description="RBAC role of requesting user ('ANALYST', 'PROCUREMENT_MANAGER', 'CPO')")
    supplier_id: Optional[str] = Field("SUP-1047", description="Optional target supplier context")
    case_id: Optional[str] = Field(None, description="Optional incident case reference")


class CopilotQueryResponse(BaseModel):
    """Evidence-grounded recommendation response with full citation lineage."""
    query: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    abstained: bool = False
    abstention_reason: Optional[str] = None
    retrieval_iterations: int = 1
    critic_sufficiency_score: float = Field(..., ge=0.0, le=1.0)
    user_role_applied: str
    prompt_version: str = "copilot-rag-v1.0"
