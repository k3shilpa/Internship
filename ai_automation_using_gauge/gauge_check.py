"""
gauge_check.py
==============
Run this to diagnose why Gauge shows Passed=0 Failed=0.
Place in project root and run:  python gauge_check.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
EXECUTION_DIR = ROOT / "execution_layer"


def check(label, cmd):
    print(f"\n[CHECK] {label}")
    print(f"  Command: {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        out = (r.stdout + r.stderr).strip()
        print(f"  Exit code: {r.returncode}")
        if out:
            print(f"  Output: {out[:300]}")
        return r.returncode == 0
    except FileNotFoundError:
        print("  RESULT: NOT FOUND (not installed or not on PATH)")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


print("=" * 55)
print("  GAUGE SETUP DIAGNOSTICS")
print("=" * 55)

# 1. Gauge binary
gauge_ok = check("Gauge binary", ["gauge", "version"])

# 2. Gauge Python plugin
check("Gauge Python plugin", ["gauge", "install", "python", "--check"])

# 3. Gauge HTML report plugin
check("Gauge HTML report plugin", ["gauge", "install", "html-report", "--check"])

# 4. List installed plugins
check("Installed plugins", ["gauge", "list", "--plugins"])

# 5. Check spec files
specs = list((EXECUTION_DIR / "specs").glob("*.spec"))
print(f"\n[CHECK] Spec files in execution_layer/specs/")
if specs:
    for s in specs:
        lines = s.read_text().count("\n## ")
        print(f"  Found: {s.name}  ({lines} scenarios)")
else:
    print("  NONE FOUND — run the pipeline first to generate specs")

# 6. Check ai_steps.py
steps_file = EXECUTION_DIR / "step_impl" / "ai_steps.py"
print(f"\n[CHECK] ai_steps.py")
if steps_file.exists():
    lines = len(steps_file.read_text().splitlines())
    print(f"  Found: {steps_file}  ({lines} lines)")
else:
    print("  NOT FOUND — step_impl_generator needs to run first")

# 7. Check manifest.json
manifest = EXECUTION_DIR / "manifest.json"
print(f"\n[CHECK] manifest.json")
if manifest.exists():
    print(f"  Found: {manifest.read_text().strip()}")
else:
    print("  NOT FOUND — run: cd execution_layer && gauge init python")

# 8. Try running gauge on the most recent spec
print(f"\n[CHECK] Try gauge run on most recent spec")
if specs and gauge_ok:
    latest = max(specs, key=lambda p: p.stat().st_mtime)
    print(f"  Running: gauge run --verbose {latest.name}")
    try:
        r = subprocess.run(
            ["gauge", "run", "--verbose", str(latest)],
            cwd=str(EXECUTION_DIR),
            capture_output=True, text=True, timeout=30,
        )
        combined = (r.stdout + r.stderr).strip()
        print(f"  Exit code: {r.returncode}")
        print(f"  Output (last 600 chars):\n{combined[-600:]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 55)
print("  FIX COMMANDS (if anything above failed):")
print("=" * 55)
print("""
  # Install Gauge (Windows)
  choco install gauge
  # OR download from https://gauge.org/get-started/

  # Install plugins
  gauge install python
  gauge install html-report
  gauge install screenshot

  # Initialize Gauge in execution_layer (if manifest.json missing)
  cd execution_layer
  gauge init python
  cd ..
""")