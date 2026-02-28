"""
executor/gauge_runner.py
========================
Executes Gauge spec files and saves pass/fail results as JSON.

HOW TO RUN (from project root):
    python executor/gauge_runner.py

ALL SETTINGS ARE HARDCODED BELOW — edit and run.
No config file, no CLI arguments, no relative imports.
"""

import json
import logging
import subprocess
import os
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
#  SETTINGS — edit these values directly
# =============================================================================

GAUGE_PROJECT_DIR = "gauge_project"                       # Gauge project root
SPECS_DIR         = "gauge_project/specs"                 # where .spec files are
RESULTS_FILE      = "gauge_project/reports/results.json"  # where to save results

# What to run:
#   "all"          → every spec file in SPECS_DIR
#   "smoke"        → only smoke_tests.spec
#   "form_tests.spec"  → a specific spec file
RUN_MODE = "all"

# Tag filter — None = no filter. e.g. "smoke" or "high"
TAGS = None

# Number of parallel workers (1 = sequential)
PARALLEL = 1

# =============================================================================

os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)


def run():
    logger.info(f"\n{'='*55}")
    logger.info(f"GAUGE RUNNER")
    logger.info(f"  mode     : {RUN_MODE}")
    logger.info(f"  tags     : {TAGS or 'none'}")
    logger.info(f"  parallel : {PARALLEL}")
    logger.info(f"{'='*55}")

    if RUN_MODE == "all":
        target = SPECS_DIR
    elif RUN_MODE == "smoke":
        smoke  = os.path.join(SPECS_DIR, "smoke_tests.spec")
        target = smoke if os.path.isfile(smoke) else SPECS_DIR
    else:
        target = os.path.join(SPECS_DIR, RUN_MODE)

    cmd = ["gauge", "run", "--machine-readable", target]
    if TAGS:
        cmd += ["--tags", TAGS]
    if PARALLEL > 1:
        cmd += ["--parallel", "-n", str(PARALLEL)]

    logger.info(f"\n  CMD: {' '.join(cmd)}\n")
    start = datetime.now()

    results = {
        "run_metadata": {
            "started_at":    start.isoformat(),
            "mode":          RUN_MODE,
            "tags":          TAGS,
            "gauge_version": _gauge_ver(),
        },
        "summary":      {},
        "spec_results": [],
    }

    try:
        proc = subprocess.run(
            cmd, cwd=GAUGE_PROJECT_DIR,
            capture_output=True, text=True, timeout=300
        )
        end = datetime.now()
        results["run_metadata"]["finished_at"]      = end.isoformat()
        results["run_metadata"]["duration_seconds"] = round((end - start).total_seconds(), 2)
        results["return_code"] = proc.returncode
        _parse_output(proc.stdout, proc.stderr, results)

        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        s  = results["summary"]
        ok = "PASSED" if proc.returncode == 0 else "FAILED"
        logger.info(f"\n{ok}  {s.get('passed',0)}/{s.get('total_scenarios',0)} passed  "
                    f"({s.get('pass_rate',0)}%)  in {results['run_metadata']['duration_seconds']}s")

    except subprocess.TimeoutExpired:
        logger.error("Timed out after 5 minutes")
        results["run_metadata"]["error"] = "timeout"
    except FileNotFoundError:
        logger.error("'gauge' command not found — install from https://gauge.org/get-started/")
        results["run_metadata"]["error"] = "gauge_not_installed"
    except Exception as ex:
        logger.error(f"Error: {ex}")
        results["run_metadata"]["error"] = str(ex)

    logger.info(f"\nResults saved → {RESULTS_FILE}")
    logger.info(f"\nNext step: set RESULTS_FILE = \"{RESULTS_FILE}\" in reports/report_generator.py")
    logger.info(f"Then: python reports/report_generator.py")


def _parse_output(stdout, stderr, results):
    results["raw_output"] = stdout[-4000:]
    results["errors"]     = stderr[-1000:] if stderr else ""
    passed = failed = skipped = 0
    specs  = []
    cur    = None

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d  = json.loads(line)
            t  = d.get("type", "")
            if t == "specStart":
                cur = {"spec": d.get("spec", ""), "scenarios": []}
            elif t == "scenarioEnd":
                st   = d.get("status", "unknown")
                scen = {"name": d.get("scenario", ""), "status": st, "duration_ms": d.get("duration", 0)}
                if st == "fail":
                    scen["failure_message"] = d.get("message", "")
                if cur:
                    cur["scenarios"].append(scen)
                if   st == "pass": passed  += 1
                elif st == "fail": failed  += 1
                else:              skipped += 1
            elif t == "specEnd" and cur:
                specs.append(cur)
                cur = None
        except json.JSONDecodeError:
            pass

    # Fallback plain-text parsing
    if passed == 0 and failed == 0:
        m = re.search(r'Scenarios:\s+(\d+)\s+executed.*?(\d+)\s+passed.*?(\d+)\s+failed',
                      stdout, re.IGNORECASE)
        if m:
            passed  = int(m.group(2))
            failed  = int(m.group(3))
            skipped = int(m.group(1)) - passed - failed

    total = passed + failed + skipped
    results["summary"]      = {
        "total_scenarios": total, "passed": passed, "failed": failed,
        "skipped": skipped, "pass_rate": round(passed / total * 100 if total else 0, 1)
    }
    results["spec_results"] = specs


def _gauge_ver():
    try:
        r = subprocess.run(["gauge", "version"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip().split("\n")[0]
    except:
        return "unknown"


if __name__ == "__main__":
    run()