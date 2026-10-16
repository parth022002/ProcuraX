"""API routes for Sprint 6: RAG Copilot, Evidence Grounding, and Citations."""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, Query

from app.schemas.copilot import (
    CopilotQueryRequest,
    CopilotQueryResponse,
    DocumentMetadata,
)
from app.services.rag_copilot.engine import copilot_engine

router = APIRouter(tags=["copilot"])


@router.post(
    "/copilot/recommend",
    summary="Generate evidence-grounded recommendation with clause citations or honest abstention",
    response_model=CopilotQueryResponse,
)
def copilot_recommend_endpoint(request: CopilotQueryRequest):
    """
    Produce grounded procurement recommendations:
    - Verifies clause-level citations against authoritative contracts/policies
    - Implements iterative retrieval with Critic sufficiency scoring
    - Strictly abstains when evidence is missing or out-of-scope
    - Blocks adversarial prompt injection attempts
    """
    return copilot_engine.answer_query(request)


@router.get(
    "/copilot/documents",
    summary="List authorized governance documents and contracts available to user role",
    response_model=List[DocumentMetadata],
)
def list_copilot_documents_endpoint(
    role: str = Query("PROCUREMENT_MANAGER", description="User RBAC role ('ANALYST', 'PROCUREMENT_MANAGER', 'CPO')"),
):
    """Retrieve metadata of ingested documents accessible under the specified RBAC permission level."""
    return copilot_engine.list_authorized_documents(user_role=role)
