"""ProcuraX Master Full Regression & Showcase Integrity Check.

Executes all automated verification suites across data, models, backends,
security isolation, decision loop replay, and frontend production builds:
1. Repository structure and file existence validation
2. Python bytecode compilation
3. Synthetic data relational integrity & contamination audit
4. Complete backend pytest test suite (106 tests across 16 suites)
5. Secret isolation and environment hygiene scanner
6. 5-minute decision loop replay pipeline
7. Frontend TypeScript check & production bundle build
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def log_step(name: str, number: int) -> None:
    print("\n" + "=" * 80)
    print(f"STEP {number}: {name.upper()}")
    print("=" * 80)


def run_command(cmd: list[str], cwd: Path | None = None, timeout_s: int = 300) -> tuple[int, str]:
    work_dir = cwd or ROOT
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, output
    except Exception as exc:
        return 1, str(exc)


def scan_for_secrets(root_dir: Path) -> list[str]:
    """Scan source files for obvious hardcoded real credentials or API tokens."""
    violations: list[str] = []
    # Patterns for potential exposed keys
    patterns = [
        re.compile(r"sk-[a-zA-Z0-9]{32,}", re.IGNORECASE),
        re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE),
        re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE),
    ]

    skip_dirs = {".git", "node_modules", ".pytest_cache", "__pycache__", "dist", ".next", "data", ".data"}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fname in filenames:
            if fname in {".env", ".env.local", ".env.example", "package-lock.json"} or fname.startswith(".env"):
                continue
            if fname.endswith((".py", ".ts", ".tsx", ".json", ".md")):
                fpath = Path(dirpath) / fname
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    for pat in patterns:
                        if pat.search(content):
                            violations.append(f"Potential secret in {fpath.relative_to(root_dir)}")
                except Exception:
                    pass

    return violations


def main() -> int:
    start_total = time.time()
    results: list[dict[str, str]] = []

    print("*" * 80)
    print("PROCURAX MASTER FULL REGRESSION & RELEASE QUALITY GATEWAY")
    print(f"Root: {ROOT}")
    print("*" * 80)

    # 1. Structure Verification
    log_step("Repository Structure & File Integrity Check", 1)
    code, out = run_command([sys.executable, "scripts/verify_repo.py"])
    if code == 0:
        print("[PASS] Repository structure verified.")
        results.append({"step": "1. Repository Structure", "status": "PASS", "detail": "All required directories and starter files present"})
    else:
        print(f"[FAIL] Repository structure error:\n{out[:500]}")
        results.append({"step": "1. Repository Structure", "status": "FAIL", "detail": out[:100]})

    # 2. Python Syntax & Compilation
    log_step("Python Bytecode & Syntax Compilation", 2)
    code, out = run_command([sys.executable, "-m", "compileall", "-q", "backend", "scripts"])
    if code == 0:
        print("[PASS] All backend and script Python files compiled successfully without syntax errors.")
        results.append({"step": "2. Python Compilation", "status": "PASS", "detail": "Syntax & bytecode clean"})
    else:
        print(f"[FAIL] Compilation errors detected:\n{out[:500]}")
        results.append({"step": "2. Python Compilation", "status": "FAIL", "detail": out[:100]})

    # 3. Data Integrity & Contamination Validator
    log_step("Synthetic Relational Integrity & SUP-1047 Leakage Audit", 3)
    code, out = run_command([sys.executable, "scripts/data_quality_validator.py"])
    if code == 0:
        print("[PASS] 8/8 tables passed schema, relational integrity, and leakage guards.")
        results.append({"step": "3. Data Integrity & Leakage", "status": "PASS", "detail": "8 tables validated, SUP-1047 holdout guard active"})
    else:
        print(f"[FAIL] Data validator failed:\n{out[:500]}")
        results.append({"step": "3. Data Integrity & Leakage", "status": "FAIL", "detail": out[:100]})

    # 4. Backend Pytest Suite
    log_step("Backend Unit & Integration Test Suite", 4)
    code, out = run_command([sys.executable, "-m", "pytest", "backend/tests", "-q"])
    if code == 0:
        # Extract passed count
        match = re.search(r"(\d+) passed", out)
        count_str = f"{match.group(1)} tests passed" if match else "All tests passed"
        print(f"[PASS] {count_str} in backend test suite.")
        results.append({"step": "4. Backend Tests", "status": "PASS", "detail": count_str})
    else:
        print(f"[FAIL] Pytest tests failed:\n{out[:500]}")
        results.append({"step": "4. Backend Tests", "status": "FAIL", "detail": "Pytest failures detected"})

    # 5. Security & Secret Hygiene
    log_step("Secret Isolation & Environment Hygiene Scanner", 5)
    violations = scan_for_secrets(ROOT)
    if not violations:
        print("[PASS] Zero hardcoded real secrets detected across codebase.")
        results.append({"step": "5. Secret Hygiene", "status": "PASS", "detail": "Clean scan, zero real credentials committed"})
    else:
        print(f"[FAIL] Potential secrets detected:\n" + "\n".join(violations[:5]))
        results.append({"step": "5. Secret Hygiene", "status": "FAIL", "detail": f"{len(violations)} issues found"})

    # 6. Showcase Replay Pipeline
    log_step("5-Minute Decision Loop Showcase Replay", 6)
    code, out = run_command([sys.executable, "scripts/run_decision_loop_replay.py"])
    if code == 0:
        print("[PASS] Complete 8-stage decision loop replay executed cleanly.")
        results.append({"step": "6. Showcase Replay", "status": "PASS", "detail": "All 8 stages (Sense to Learn) passed"})
    else:
        print(f"[FAIL] Showcase replay failed:\n{out[:500]}")
        results.append({"step": "6. Showcase Replay", "status": "FAIL", "detail": "Replay pipeline error"})

    # 7. Frontend TypeScript & Production Build
    log_step("Frontend TypeScript & Production Build", 7)
    frontend_dir = ROOT / "frontend"
    if (frontend_dir / "package.json").exists():
        # Test npm run build
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        code, out = run_command([npm_cmd, "run", "build"], cwd=frontend_dir, timeout_s=90)
        if code == 0:
            print("[PASS] Frontend built cleanly into dist/ with zero TypeScript errors.")
            results.append({"step": "7. Frontend Production Build", "status": "PASS", "detail": "TypeScript + Vite production bundle clean"})
        else:
            print(f"[FAIL] Frontend build failed:\n{out[:500]}")
            results.append({"step": "7. Frontend Production Build", "status": "FAIL", "detail": "Build failure"})
    else:
        print("[WARN] frontend/package.json not found; skipping frontend build.")
        results.append({"step": "7. Frontend Production Build", "status": "NOT VERIFIED", "detail": "Directory not found"})

    # Overall Summary Scorecard
    total_elapsed = time.time() - start_total
    all_passed = all(r["status"] == "PASS" for r in results)

    print("\n" + "=" * 80)
    print("PROCURAX REGRESSION SCORECARD & RELEASE READINESS REPORT")
    print("=" * 80)
    for r in results:
        status_tag = f"[{r['status']}]".ljust(8)
        print(f"{status_tag} {r['step'].ljust(35)} : {r['detail']}")
    print("-" * 80)
    print(f"Total Execution Time: {total_elapsed:.2f}s")
    if all_passed:
        print("OVERALL RESULT: [PASS] -- ALL GATES MET. READY FOR PUBLIC SHOWCASE.")
        print("=" * 80)
        return 0
    else:
        print("OVERALL RESULT: [FAIL] -- ONE OR MORE GATES FAILED.")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
