# run_ai_pipeline.py
# Mini pipeline — runs AI Layer 1, 2, 3 in sequence.
#
# Usage:
#   python run_ai_pipeline.py              # run all 3 layers
#   python run_ai_pipeline.py --from 2    # start from Layer 2 (skip Layer 1)
#   python run_ai_pipeline.py --from 3    # start from Layer 3 only

import argparse
import json
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
logger = logging.getLogger("ai_pipeline")


def _banner(text: str):
    print("\n" + "═" * 55)
    print(f"  {text}")
    print("═" * 55)


def _load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _check_exists(path: str, label: str):
    """Exit with a clear message if a required input file is missing."""
    if not os.path.exists(path):
        print(f"\n✗ {label} not found at: {path}")
        print("  Run the previous step first.")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# Layer runners
# ══════════════════════════════════════════════════════════════════════════════

def run_layer1():
    _banner("Layer 1 — Page Understanding")
    _check_exists(config.DOM_DATA_PATH, "DOM data (crawler output)")

    from ai_layers.layer1_page_understanding import analyse_all_pages
    dom_data = _load_json(config.DOM_DATA_PATH)
    logger.info(f"Loaded {len(dom_data)} pages from DOM data")

    analyses = analyse_all_pages(dom_data)
    logger.info(f"✓ Layer 1 complete — {len(analyses)} pages analysed")
    return analyses


def run_layer2(page_analyses=None):
    _banner("Layer 2 — Field & Form Analysis")
    _check_exists(config.DOM_DATA_PATH,      "DOM data (crawler output)")
    _check_exists(config.PAGE_ANALYSIS_PATH, "Page analysis (Layer 1 output)")

    from ai_layers.layer2_field_analysis import analyse_all_fields
    dom_data      = _load_json(config.DOM_DATA_PATH)
    page_analyses = page_analyses or _load_json(config.PAGE_ANALYSIS_PATH)

    analyses = analyse_all_fields(dom_data, page_analyses)
    pages_with_forms = sum(1 for a in analyses if a.get("forms"))
    logger.info(f"✓ Layer 2 complete — {pages_with_forms} pages with forms found")
    return analyses


def run_layer3(page_analyses=None, field_analyses=None):
    _banner("Layer 3 — Test Strategy Generation (with RAG)")
    _check_exists(config.PAGE_ANALYSIS_PATH,  "Page analysis (Layer 1 output)")
    _check_exists(config.FIELD_ANALYSIS_PATH, "Field analysis (Layer 2 output)")

    from ai_layers.layer3_strategy import generate_all_strategies
    from rag.retriever import Retriever

    page_analyses  = page_analyses  or _load_json(config.PAGE_ANALYSIS_PATH)
    field_analyses = field_analyses or _load_json(config.FIELD_ANALYSIS_PATH)

    # Build RAG index
    retriever = Retriever()
    try:
        retriever.build_index()
        logger.info(f"RAG index built — {len(retriever.store)} entries")
    except Exception as e:
        logger.warning(f"RAG indexing failed ({e}) — continuing without RAG")
        retriever = None

    strategies = generate_all_strategies(page_analyses, field_analyses, retriever)
    total = sum(len(s.get("test_scenarios", [])) for s in strategies)
    logger.info(f"✓ Layer 3 complete — {total} scenarios across {len(strategies)} pages")
    return strategies


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Mini AI pipeline — runs Layer 1, 2, 3 in sequence"
    )
    parser.add_argument(
        "--from", dest="start_from", type=int, default=1, choices=[1, 2, 3],
        help="Which layer to start from (default: 1)"
    )
    args = parser.parse_args()

    start = datetime.now()
    _banner(f"AI Mini Pipeline — starting from Layer {args.start_from}")

    os.makedirs(config.DATA_DIR, exist_ok=True)

    page_analyses  = None
    field_analyses = None

    if args.start_from <= 1:
        page_analyses = run_layer1()

    if args.start_from <= 2:
        field_analyses = run_layer2(page_analyses)

    if args.start_from <= 3:
        run_layer3(page_analyses, field_analyses)

    elapsed = (datetime.now() - start).total_seconds()
    _banner(f"✓ AI Pipeline complete — {elapsed:.1f}s")
    print(f"  Page analysis  : {config.PAGE_ANALYSIS_PATH}")
    print(f"  Field analysis : {config.FIELD_ANALYSIS_PATH}")
    print(f"  Test strategy  : {config.TEST_STRATEGY_PATH}")
    print()
    print("  Next steps:")
    print("    python gauge_builder/gauge_generator.py")
    print("    python gauge_builder/step_impl_generator.py")
    print("    gauge run specs")
    print()


if __name__ == "__main__":
    main()
