# execution/result_parser.py - Parse Gauge XML results into structured JSON

import json
import logging
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


def run_gauge(spec_path: str = None) -> subprocess.CompletedProcess:
    """Execute Gauge and return the completed process."""
    spec_path = spec_path or config.GENERATED_SPEC_PATH
    cmd = [
        "gauge", "run",
        "--format", "xml",
        "--dir", config.BASE_DIR,
        spec_path,
    ]
    logger.info(f"Running Gauge: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=config.BASE_DIR)
    logger.info(f"Gauge exit code: {result.returncode}")
    if result.stdout:
        logger.debug(result.stdout[-2000:])
    if result.stderr:
        logger.warning(result.stderr[-1000:])
    return result


def parse_xml_results(xml_path: str = None) -> list[dict]:
    """
    Parse the Gauge XML results file into a list of scenario result dicts.
    Gauge writes results to reports/xml-report/result.xml by default.
    """
    if xml_path is None:
        xml_path = os.path.join(config.REPORTS_DIR, "xml-report", "result.xml")

    if not os.path.exists(xml_path):
        logger.warning(f"XML results file not found at {xml_path}")
        return []

    results = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for spec_el in root.findall(".//specification"):
            spec_name = spec_el.get("name", "")
            for scenario_el in spec_el.findall(".//scenario"):
                scenario_name = scenario_el.get("name", "")
                failed = scenario_el.get("failed", "false").lower() == "true"
                duration = scenario_el.get("duration", "0")

                # Extract failure message if any
                failure_reason = ""
                for err_el in scenario_el.findall(".//error-message"):
                    failure_reason = err_el.text or ""
                    break

                results.append({
                    "spec": spec_name,
                    "scenario": scenario_name,
                    "status": "failed" if failed else "passed",
                    "duration_ms": int(duration),
                    "failure_reason": failure_reason,
                    "timestamp": datetime.now().isoformat(),
                })
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML: {e}")

    return results


def save_results(results: list[dict], path: str = None):
    """Persist parsed results to JSON."""
    path = path or config.EXECUTION_RESULTS_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Merge with existing results
    existing = []
    if os.path.exists(path):
        try:
            with open(path) as f:
                existing = json.load(f)
        except Exception:
            pass

    combined = existing + results
    with open(path, "w") as f:
        json.dump(combined, f, indent=2)

    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    logger.info(f"Results saved: {passed} passed, {failed} failed → {path}")


def print_summary(results: list[dict]):
    """Print a human-readable results summary."""
    if not results:
        print("No results to display.")
        return

    passed = [r for r in results if r["status"] == "passed"]
    failed = [r for r in results if r["status"] == "failed"]
    total  = len(results)

    print("\n" + "═" * 60)
    print(f"  GAUGE TEST RESULTS SUMMARY")
    print("═" * 60)
    print(f"  Total:  {total}")
    print(f"  ✓ Passed: {len(passed)}")
    print(f"  ✗ Failed: {len(failed)}")
    print(f"  Pass rate: {len(passed)/total*100:.1f}%" if total else "")
    print("═" * 60)

    if failed:
        print("\nFailed Scenarios:")
        for r in failed:
            print(f"  ✗ [{r['spec']}] {r['scenario']}")
            if r.get("failure_reason"):
                print(f"      ↳ {r['failure_reason'][:120]}")
    print()
