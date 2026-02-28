#!/usr/bin/env python3
# main_pipeline.py - AI-Driven Automated Exploratory Testing Pipeline
#
# Pipeline stages:
#   1. Crawl       → DOM extraction via Selenium Chrome
#   2. Layer 1     → Page understanding (Ollama AI)
#   3. Layer 2     → Field/form analysis (Ollama AI)
#   4. RAG         → Index knowledge base, retrieve context
#   5. Layer 3     → Test strategy generation (Ollama AI)
#   6. Gauge Build → .spec file generation
#   7. Execute     → Run Gauge, parse results

import argparse
import json
import logging
import os
import sys
from datetime import datetime

import config

# ── Logging setup ─────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("pipeline")

# ── Imports ───────────────────────────────────────────────────────────────────
from ai_layers.ai_utils import check_ollama_health
from crawler.dom_crawler import crawl
from ai_layers.layer1_page_understanding import analyse_all_pages
from ai_layers.layer2_field_analysis import analyse_all_fields
from ai_layers.layer3_strategy import generate_all_strategies
from rag.retriever import Retriever
from gauge_builder.gauge_generator import generate_combined_spec
from execution.spec_builder import write_step_impl
from execution.result_parser import run_gauge, parse_xml_results, save_results, print_summary


def _banner(text: str):
    width = 60
    print("\n" + "═" * width)
    print(f"  {text}")
    print("═" * width)


def _load_json(path: str, default=None):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default or []


def run_pipeline(
    target_url: str = None,
    skip_crawl: bool = False,
    skip_execute: bool = False,
    resume: bool = False,
):
    start_time = datetime.now()

    target_url = target_url or config.TARGET_URL
    _banner(f"AI-Driven Gauge Tester | {target_url}")

    # ── Pre-flight ─────────────────────────────────────────────────────────────
    _banner("0. Pre-flight Checks")
    if not check_ollama_health():
        logger.error("Ollama is not available. Please start Ollama and ensure the model is pulled.")
        sys.exit(1)

    # Ensure directories exist
    for d in [config.DATA_DIR, config.REPORTS_DIR, config.SPECS_DIR, os.path.dirname(config.LOG_FILE)]:
        os.makedirs(d, exist_ok=True)

    # ── Stage 1: Crawl ─────────────────────────────────────────────────────────
    _banner("1. Crawling Target Application")
    if skip_crawl and os.path.exists(config.DOM_DATA_PATH):
        logger.info("Skipping crawl — loading existing DOM data.")
        dom_data = _load_json(config.DOM_DATA_PATH)
    else:
        dom_data = crawl(start_url=target_url)

    logger.info(f"→ {len(dom_data)} pages collected.")

    # ── Stage 2: Layer 1 — Page Understanding ─────────────────────────────────
    _banner("2. AI Layer 1 — Page Understanding")
    if resume and os.path.exists(config.PAGE_ANALYSIS_PATH):
        logger.info("Resuming — loading existing page analyses.")
        page_analyses = _load_json(config.PAGE_ANALYSIS_PATH)
    else:
        page_analyses = analyse_all_pages(dom_data)

    logger.info(f"→ {len(page_analyses)} pages analysed.")

    # ── Stage 3: Layer 2 — Field Analysis ─────────────────────────────────────
    _banner("3. AI Layer 2 — Field & Form Analysis")
    if resume and os.path.exists(config.FIELD_ANALYSIS_PATH):
        logger.info("Resuming — loading existing field analyses.")
        field_analyses = _load_json(config.FIELD_ANALYSIS_PATH)
    else:
        field_analyses = analyse_all_fields(dom_data, page_analyses)

    pages_with_forms = sum(1 for f in field_analyses if f.get("forms"))
    logger.info(f"→ {pages_with_forms} pages with forms analysed.")

    # ── Stage 4: RAG — Index Knowledge Base ───────────────────────────────────
    _banner("4. RAG — Indexing Knowledge Base")
    retriever = Retriever()
    try:
        retriever.build_index()
        logger.info(f"→ Knowledge base indexed ({len(retriever.store)} entries).")
    except Exception as e:
        logger.warning(f"RAG indexing failed (non-fatal): {e}")
        retriever = None

    # ── Stage 5: Layer 3 — Test Strategy ──────────────────────────────────────
    _banner("5. AI Layer 3 — Test Strategy Generation")
    if resume and os.path.exists(config.TEST_STRATEGY_PATH):
        logger.info("Resuming — loading existing strategies.")
        strategies = _load_json(config.TEST_STRATEGY_PATH)
    else:
        strategies = generate_all_strategies(page_analyses, field_analyses, retriever)

    total_scenarios = sum(len(s.get("test_scenarios", [])) for s in strategies)
    logger.info(f"→ {total_scenarios} test scenarios generated across {len(strategies)} pages.")

    # ── Stage 6: Build Gauge Spec ──────────────────────────────────────────────
    _banner("6. Building Gauge .spec File")
    spec_content = generate_combined_spec(strategies)
    logger.info(f"→ Spec written to {config.GENERATED_SPEC_PATH}")

    # Write step_impl.py
    write_step_impl()
    logger.info(f"→ step_impl.py generated.")

    # ── Stage 7: Execute ───────────────────────────────────────────────────────
    if skip_execute:
        _banner("7. Execution Skipped (--no-execute flag)")
        logger.info("To run manually: gauge run specs/generated_test.spec")
    else:
        _banner("7. Executing Gauge Tests")
        proc = run_gauge(config.GENERATED_SPEC_PATH)
        results = parse_xml_results()
        if results:
            save_results(results)
            print_summary(results)
        else:
            logger.warning("No parsed results found. Check Gauge output above.")
            if proc.returncode != 0:
                logger.error("Gauge exited with non-zero code. Check logs.")

    # ── Done ───────────────────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    _banner(f"Pipeline Complete — {elapsed:.1f}s")
    print(f"  Spec file  : {config.GENERATED_SPEC_PATH}")
    print(f"  Data dir   : {config.DATA_DIR}")
    print(f"  Reports    : {config.REPORTS_DIR}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="AI-Driven Automated Exploratory Testing with Gauge + Ollama"
    )
    parser.add_argument("--url",           default=None,        help="Target URL to test (overrides config)")
    parser.add_argument("--no-crawl",      action="store_true", help="Skip crawling; reuse existing DOM data")
    parser.add_argument("--no-execute",    action="store_true", help="Generate spec but don't run Gauge")
    parser.add_argument("--resume",        action="store_true", help="Resume from last AI analysis checkpoint")
    parser.add_argument("--model",         default=None,        help="Override Ollama model (e.g. mistral)")
    parser.add_argument("--depth",         default=None, type=int, help="Crawl depth (default from config)")
    parser.add_argument("--max-pages",     default=None, type=int, help="Max pages to crawl")

    args = parser.parse_args()

    # Apply CLI overrides to config
    if args.model:
        config.OLLAMA_MODEL = args.model
    if args.depth:
        config.MAX_CRAWL_DEPTH = args.depth
    if args.max_pages:
        config.MAX_PAGES = args.max_pages

    run_pipeline(
        target_url=args.url,
        skip_crawl=args.no_crawl,
        skip_execute=args.no_execute,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
