"""Signal freshness calculation and age classification utilities."""
from __future__ import annotations

from datetime import datetime, timezone
import dateutil.parser


def calculate_signal_freshness(timestamp_str: str | None) -> tuple[str, float | None]:
    """Calculate the age in hours and assign a freshness tier.

    Tiers:
    - fresh: < 24 hours
    - recent: 24 to 72 hours
    - stale: 72 to 168 hours (7 days)
    - archived: >= 168 hours
    """
    if not timestamp_str:
        return "unknown", None

    try:
        # Handle formats like 20260925T140000Z or standard ISO 8601
        dt = dateutil.parser.parse(timestamp_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        diff_seconds = (now - dt).total_seconds()
        if diff_seconds < 0:
            diff_seconds = 0
            
        age_hours = round(diff_seconds / 3600.0, 1)

        if age_hours < 24.0:
            status = "fresh"
        elif age_hours < 72.0:
            status = "recent"
        elif age_hours < 168.0:
            status = "stale"
        else:
            status = "archived"

        return status, age_hours
    except Exception:
        return "unknown", None
