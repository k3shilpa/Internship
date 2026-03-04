"""
debug_gauge.py
==============
Runs gauge directly on the most recent spec and prints the FULL output
so we can see exactly why scenarios are being skipped.

Run from project root:
    python debug_gauge.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT          = Path(__file__).parent
EXECUTION_DIR = ROOT / "execution_layer"
SPECS_DIR     = EXECUTION_DIR / "specs"
STEP_IMPL_DIR = EXECUTION_DIR / "step_impl"


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── 1. Find most recent spec ──────────────────────────────────────────────────
section("Most Recent Spec")
specs = sorted(SPECS_DIR.glob("*.spec"), key=lambda p: p.stat().st_mtime, reverse=True)
if not specs:
    print("  No spec files found. Run main_pipeline.py first.")
    sys.exit(1)

latest_spec = specs[0]
print(f"  File: {latest_spec}")
print(f"\n  Contents (first 40 lines):")
lines = latest_spec.read_text(encoding="utf-8").splitlines()
for i, line in enumerate(lines[:40], 1):
    print(f"    {i:3}: {line}")


# ── 2. Show ai_steps.py ───────────────────────────────────────────────────────
section("ai_steps.py")
ai_steps = STEP_IMPL_DIR / "ai_steps.py"
if ai_steps.exists():
    step_lines = ai_steps.read_text(encoding="utf-8").splitlines()
    print(f"  File: {ai_steps}  ({len(step_lines)} lines)")
    # Show all @step decorators
    print("\n  Registered steps:")
    for line in step_lines:
        if line.strip().startswith("@step("):
            print(f"    {line.strip()}")
else:
    print("  NOT FOUND")
    sys.exit(1)


# ── 3. Show manifest.json ─────────────────────────────────────────────────────
section("manifest.json")
manifest = EXECUTION_DIR / "manifest.json"
if manifest.exists():
    print(f"  Content: {manifest.read_text(encoding='utf-8')}")
else:
    print("  NOT FOUND — creating now...")
    manifest.write_text(json.dumps({
        "Language": "python",
        "Plugins": ["html-report", "screenshot"]
    }, indent=2))
    print(f"  Created: {manifest}")


# ── 4. Show default.properties ────────────────────────────────────────────────
section("default.properties")
props = EXECUTION_DIR / "env" / "default" / "default.properties"
if props.exists():
    print(f"  Content:\n  {props.read_text(encoding='utf-8')}")
else:
    print("  NOT FOUND — creating now...")
    props.parent.mkdir(parents=True, exist_ok=True)
    props.write_text(
        f"BASE_URL = https://calculators.net\n"
        f"gauge_screenshots_dir = {ROOT / 'reports' / 'screenshots'}\n"
        f"gauge_reports_dir = {ROOT / 'reports'}\n"
    )
    print(f"  Created: {props}")


# ── 5. Show all files in step_impl/ ──────────────────────────────────────────
section("Files in execution_layer/step_impl/")
for f in sorted(STEP_IMPL_DIR.iterdir()):
    print(f"  {f.name}  ({f.stat().st_size} bytes)")


# ── 6. Run gauge with full verbose output ────────────────────────────────────
section("Running Gauge (full output)")
print(f"  cwd: {EXECUTION_DIR}")
print(f"  cmd: gauge run --verbose {latest_spec.name}\n")

result = subprocess.run(
    ["gauge", "run", "--verbose", str(latest_spec)],
    cwd=str(EXECUTION_DIR),
    capture_output=True,
    text=True,
    timeout=120,
)

print("  ── STDOUT ──")
print(result.stdout if result.stdout.strip() else "  (empty)")
print("\n  ── STDERR ──")
print(result.stderr if result.stderr.strip() else "  (empty)")
print(f"\n  Exit code: {result.returncode}")


# ── 7. Try gauge run --simple-console for cleaner output ─────────────────────
section("Running Gauge (simple console)")
result2 = subprocess.run(
    ["gauge", "run", "--simple-console", str(latest_spec)],
    cwd=str(EXECUTION_DIR),
    capture_output=True,
    text=True,
    timeout=120,
)
print(result2.stdout[-2000:] if result2.stdout else "(empty)")
print(result2.stderr[-1000:] if result2.stderr else "")


# ── 8. Check if Python in gauge env matches venv ─────────────────────────────
section("Python Environment Check")
result3 = subprocess.run(
    ["python", "--version"],
    cwd=str(EXECUTION_DIR),
    capture_output=True, text=True
)
print(f"  gauge cwd python: {(result3.stdout + result3.stderr).strip()}")
print(f"  current python:   {sys.version}")
print(f"  current exe:      {sys.executable}")

# Check if getgauge is importable
try:
    import getgauge
    print(f"  getgauge:         FOUND (version: {getgauge.__version__ if hasattr(getgauge,'__version__') else 'unknown'})")
except ImportError:
    print("  getgauge:         NOT FOUND — run: pip install getgauge")