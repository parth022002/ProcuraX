from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(ROOT / ".env")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(provider: str, data: Any) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RAW_DIR / f"{provider}_{stamp}.json"
    wrapper = {"provider": provider, "retrieved_at_utc": utc_now_iso(), "data": data}
    path.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def save_csv(provider: str, rows: list[dict[str, Any]]) -> Path | None:
    if not rows:
        print(f"[{provider}] No rows returned; no CSV created.")
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RAW_DIR / f"{provider}_{stamp}.csv"
    pd.json_normalize(rows, sep=".").to_csv(path, index=False, encoding="utf-8-sig")
    return path


def request_json(url: str, *, params: dict[str, Any] | None = None,
                 headers: dict[str, str] | None = None, timeout: int = 30) -> dict[str, Any] | list[Any]:
    import requests

    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as exc:
        preview = response.text[:300]
        raise RuntimeError(f"Expected JSON from {response.url}; got: {preview}") from exc
