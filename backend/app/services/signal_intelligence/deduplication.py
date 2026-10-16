"""Deduplication and corroboration engine for signal intelligence."""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

from app.services.signal_intelligence.schema import NormalizedSignal


def canonicalize_url(url: str) -> str:
    """Strip tracking parameters, fragments, and normalize schema/host."""
    if not url:
        return ""
    parsed = urlparse(url)
    clean_host = parsed.netloc.lower().replace("www.", "")
    clean_path = re.sub(r"/+", "/", parsed.path).rstrip("/")
    return f"{clean_host}{clean_path}"


def compute_content_hash(provider: str, url: str, title: str) -> str:
    """Generate deterministic SHA256 content hash."""
    clean_url = canonicalize_url(url)
    clean_title = re.sub(r"\W+", " ", title or "").strip().lower()
    payload = f"{clean_url}|{clean_title}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def deduplicate_signals(signals: list[NormalizedSignal]) -> list[NormalizedSignal]:
    """Collapse duplicate signals sharing canonical URLs or content hashes while tracking corroboration."""
    seen_hashes: dict[str, NormalizedSignal] = {}

    for sig in signals:
        h = sig.content_hash or compute_content_hash(sig.provider, sig.canonical_url, sig.title)
        sig.content_hash = h

        if h not in seen_hashes:
            seen_hashes[h] = sig
        else:
            existing = seen_hashes[h]
            # Retain corroboration count in raw_metadata
            corroboration = existing.raw_metadata.get("corroboration_count", 1) + 1
            existing.raw_metadata["corroboration_count"] = corroboration
            # If incoming has higher mapping confidence, adopt it
            if sig.mapping_confidence > existing.mapping_confidence:
                existing.mapped_supplier_id = sig.mapped_supplier_id
                existing.mapping_confidence = sig.mapping_confidence
                existing.scenario_disclaimer = sig.scenario_disclaimer

    return list(seen_hashes.values())
