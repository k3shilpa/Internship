# run_gauge_pipeline.py
# Mini pipeline — runs gauge_generator and step_impl_generator in sequence.
#
# Usage:
#   python run_gauge_pipeline.py              # run both steps
#   python run_gauge_pipeline.py --from 2    # run only step_impl_generator

import argparse
import logging
import os
import sys
from datetime import datetime

import config

# ── Logging ───────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("gauge_pipeline")


def _banner(text: str):
    print("\n" + "═" * 55)
    print(f"  {text}")
    print("═" * 55)


def _check_exists(path: str, label: str):
    """Exit with a clear message if a required input file is missing."""
    if not os.path.exists(path):
        print(f"\n✗ {label} not found at: {path}")
        print("  Run the previous step first.")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# Step runners
# ══════════════════════════════════════════════════════════════════════════════

def run_gauge_generator():
    _banner("Step 1 — Generating Gauge .spec file")
    _check_exists(config.TEST_STRATEGY_PATH, "Test strategy (Layer 3 output)")

    from gauge_builder.gauge_generator import generate_combined_spec
    import json

    with open(config.TEST_STRATEGY_PATH, encoding="utf-8") as f:
        strategies = json.load(f)

    logger.info(f"Loaded {len(strategies)} strategies from {config.TEST_STRATEGY_PATH}")

    spec = generate_combined_spec(strategies)

    logger.info(f"✓ Spec file written to: {config.GENERATED_SPEC_PATH}")
    return spec


def run_step_impl_generator():
    _banner("Step 2 — Generating step_impl.py from spec")
    _check_exists(config.GENERATED_SPEC_PATH, "Spec file (gauge_generator output)")

    from gauge_builder.step_impl_generator import generate_step_impl

    generate_step_impl(
        spec_path=config.GENERATED_SPEC_PATH,
        output_path=os.path.join(config.BASE_DIR, "step_impl", "step_impl.py"),
    )

    logger.info(f"✓ step_impl.py written to: {os.path.join(config.BASE_DIR, 'step_impl', 'step_impl.py')}")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Mini Gauge pipeline — generates spec and step_impl.py"
    )
    parser.add_argument(
        "--from", dest="start_from", type=int, default=1, choices=[1, 2],
        help="1 = gauge_generator + step_impl_generator (default), 2 = step_impl_generator only"
    )
    args = parser.parse_args()

    start = datetime.now()
    _banner(f"Gauge Mini Pipeline — starting from Step {args.start_from}")

    os.makedirs(config.SPECS_DIR, exist_ok=True)

    if args.start_from <= 1:
        run_gauge_generator()

    if args.start_from <= 2:
        run_step_impl_generator()

    elapsed = (datetime.now() - start).total_seconds()
    _banner(f"✓ Gauge Pipeline complete — {elapsed:.1f}s")
    print(f"  Spec file    : {config.GENERATED_SPEC_PATH}")
    print(f"  Step impl    : {os.path.join(config.BASE_DIR, 'step_impl', 'step_impl.py')}")
    print()
    print("  Next step:")
    print("    gauge run specs")
    print()


if __name__ == "__main__":
    main()
