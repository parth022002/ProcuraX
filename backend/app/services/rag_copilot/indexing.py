"""Structure-aware chunking and RBAC-governed indexing for RAG Copilot."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Set

from app.schemas.copilot import DocumentMetadata
from app.services.rag_copilot.corpus import RAW_DOCUMENTS

# RBAC permission hierarchy
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "CPO": {"ALL", "PROCUREMENT_MANAGER", "CPO"},
    "PROCUREMENT_MANAGER": {"ALL", "PROCUREMENT_MANAGER"},
    "ANALYST": {"ALL"},
}


@dataclass(frozen=True)
class DocumentChunk:
    """Structure-aware clause chunk with metadata and access control tag."""
    chunk_id: str
    document_id: str
    document_title: str
    version: str
    section: str
    access_level: str
    content: str
    category: str


class DocumentIndex:
    """In-memory hybrid retrieval index with strict role-based access filtering."""

    def __init__(self, raw_documents: List[Dict]):
        self.chunks: List[DocumentChunk] = []
        self.metadata_registry: List[DocumentMetadata] = []
        self._build_index(raw_documents)

    def _build_index(self, raw_documents: List[Dict]) -> None:
        """Parse raw documents into searchable chunks."""
        for doc in raw_documents:
            doc_id = doc["document_id"]
            title = doc["title"]
            version = doc["version"]
            effective_date = doc["effective_date"]
            access_level = doc["access_level"]
            category = doc["category"]
            sections = doc.get("sections", [])

            for idx, sec in enumerate(sections):
                chunk_id = f"CHK-{doc_id}-{idx+1}"
                self.chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=doc_id,
                        document_title=title,
                        version=version,
                        section=sec["section"],
                        access_level=access_level,
                        content=sec["content"],
                        category=category,
                    )
                )

            self.metadata_registry.append(
                DocumentMetadata(
                    document_id=doc_id,
                    title=title,
                    version=version,
                    effective_date=effective_date,
                    access_level=access_level,
                    category=category,
                    total_chunks=len(sections),
                )
            )

    def get_authorized_chunks(self, user_role: str) -> List[DocumentChunk]:
        """Filter chunks based on requesting user's RBAC role."""
        allowed_levels = ROLE_PERMISSIONS.get(user_role.upper(), {"ALL"})
        return [c for c in self.chunks if c.access_level in allowed_levels]

    def search(
        self,
        query: str,
        user_role: str = "PROCUREMENT_MANAGER",
        top_k: int = 4,
    ) -> List[tuple[DocumentChunk, float]]:
        """
        Hybrid keyword-overlap search with RBAC context gating.
        Returns list of (chunk, relevance_score) sorted descending by relevance.
        """
        authorized = self.get_authorized_chunks(user_role)
        query_tokens = set(re.findall(r"\w+", query.lower()))

        scored_chunks: List[tuple[DocumentChunk, float]] = []

        for chunk in authorized:
            content_tokens = set(re.findall(r"\w+", chunk.content.lower()))
            section_tokens = set(re.findall(r"\w+", chunk.section.lower()))
            title_tokens = set(re.findall(r"\w+", chunk.document_title.lower()))

            all_chunk_tokens = content_tokens | section_tokens | title_tokens
            overlap = query_tokens & all_chunk_tokens

            if not overlap:
                continue

            # Weight token overlap with length normalization
            content_overlap = len(query_tokens & content_tokens)
            title_overlap = len(query_tokens & (title_tokens | section_tokens))
            score = (content_overlap * 1.0 + title_overlap * 2.0) / (len(query_tokens) + 1.0)
            scored_chunks.append((chunk, round(score, 4)))

        # Sort descending by relevance score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]


index = DocumentIndex(RAW_DOCUMENTS)
