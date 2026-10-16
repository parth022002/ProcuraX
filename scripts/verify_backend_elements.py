"""Comprehensive Backend Elements & Database Connectivity Verification Script."""
import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_endpoint(name: str, method: str, path: str, payload: dict = None, headers: dict = None):
    url = f"{BASE_URL}{path}"
    headers = headers or {}
    headers.setdefault("x-bypass-rate-limit", "test-bypass")
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed_ms = (time.time() - start) * 1000
            body = resp.read().decode("utf-8")
            try:
                parsed = json.loads(body)
                summary = f"JSON object with keys: {list(parsed.keys())[:5]}" if isinstance(parsed, dict) else f"JSON array ({len(parsed)} items)"
            except Exception:
                summary = f"Text ({len(body)} chars)"
            trace_id = resp.headers.get("X-Trace-ID", "N/A")
            return {
                "name": name,
                "endpoint": f"{method} {path}",
                "status_code": resp.status,
                "status": "PASS",
                "elapsed_ms": round(elapsed_ms, 1),
                "trace_id": trace_id,
                "detail": summary,
            }
    except urllib.error.HTTPError as err:
        elapsed_ms = (time.time() - start) * 1000
        return {
            "name": name,
            "endpoint": f"{method} {path}",
            "status_code": err.code,
            "status": "FAIL",
            "elapsed_ms": round(elapsed_ms, 1),
            "trace_id": err.headers.get("X-Trace-ID", "N/A"),
            "detail": f"HTTP Error {err.code}: {err.reason}",
        }
    except Exception as exc:
        elapsed_ms = (time.time() - start) * 1000
        return {
            "name": name,
            "endpoint": f"{method} {path}",
            "status_code": 0,
            "status": "ERROR",
            "elapsed_ms": round(elapsed_ms, 1),
            "trace_id": "N/A",
            "detail": str(exc),
        }

def run_backend_audit():
    tests = [
        # 1. Health & Database
        ("Process Health", "GET", "/health"),
        ("Neon Lakebase Postgres Health", "GET", "/health/database"),
        
        # 2. Supplier Data Foundation
        ("Suppliers List", "GET", "/suppliers"),
        ("Supplier 360 (SUP-1047)", "GET", "/suppliers/SUP-1047/360"),
        
        # 3. Risk Intelligence
        ("Risk Score Calculation", "GET", "/risk/score?supplier_id=SUP-1047"),
        ("ML Model Card", "GET", "/risk/model-card"),
        
        # 4. External Signals Intelligence
        ("External Signals List", "GET", "/signals"),
        ("Signal Providers List", "GET", "/signals/providers"),
        ("Signal Providers Telemetry", "GET", "/signals/providers/health"),
        
        # 5. Deterministic Impact Engine
        ("Supplier Impact (SUP-1047)", "GET", "/impact/supplier/SUP-1047"),
        ("Supply Network Traversal", "GET", "/impact/network/SUP-1047"),
        ("Impact Calculation Engine", "POST", "/impact/calculate", {"supplier_id": "SUP-1047", "disruption_days": 14}),
        
        # 6. Scenario Studio & Solver
        ("Scenario Generation", "POST", "/scenarios/generate", {"supplier_id": "SUP-1047", "disruption_days": 14}),
        ("Contract Constraints", "GET", "/scenarios/constraints/SUP-1047"),
        
        # 7. Grounded RAG Copilot
        ("Copilot Document Corpus", "GET", "/copilot/documents"),
        ("Evidence-Grounded Recommendation", "POST", "/copilot/recommend", {
            "query": "What are our contractual options for secondary supplier activation on harness assemblies?",
            "supplier_id": "SUP-1047"
        }),
        
        # 8. Governed State Machine Orchestrator
        ("Disruption Cases List", "GET", "/cases"),
        ("Disruption Case Lifecycle Replay", "POST", "/cases/run", {
            "supplier_id": "SUP-1047",
            "disruption_type": "FIRE",
            "expected_days": 14
        }),
    ]

    print("=" * 85)
    print("PROCURAX LIVE BACKEND ELEMENTS & DATABASE AUDIT")
    print("=" * 85)
    
    results = []
    for name, method, path, *rest in tests:
        payload = rest[0] if len(rest) > 0 else None
        res = test_endpoint(name, method, path, payload)
        results.append(res)
        status_tag = f"[{res['status']}]".ljust(7)
        print(f"{status_tag} {res['name'].ljust(35)} {res['endpoint'].ljust(32)} {res['elapsed_ms']}ms (Trace: {res['trace_id']})")
    
    print("-" * 85)
    all_pass = all(r["status"] == "PASS" for r in results)
    print(f"Total Endpoints Audited: {len(results)} | Passed: {sum(1 for r in results if r['status'] == 'PASS')} | Failed: {sum(1 for r in results if r['status'] != 'PASS')}")
    print(f"Overall Backend Status: {'ALL SYSTEMS OPERATIONAL (PASS)' if all_pass else 'ISSUES DETECTED (FAIL)'}")
    print("=" * 85)

if __name__ == "__main__":
    run_backend_audit()
