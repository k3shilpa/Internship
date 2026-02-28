# ai_layers/layer1_page_understanding.py - AI Layer 1: Page Understanding

import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ai_layers.ai_utils import call_ollama_json
from ai_layers.prompt_templates import LAYER1_SYSTEM, LAYER1_PROMPT

logger = logging.getLogger(__name__)


def analyse_page(page_dom: dict) -> dict:
    """
    Layer 1: Takes raw DOM data for a single page and returns a semantic
    understanding of the page's purpose, structure, and testability.
    """
    logger.info(f"[Layer 1] Analysing page: {page_dom.get('url', 'unknown')}")

    # Prepare a compact version of DOM for the prompt (avoid token overflow)
    compact_dom = {
        "url": page_dom.get("url"),
        "title": page_dom.get("title"),
        "forms_count": len(page_dom.get("forms", [])),
        "inputs_count": len(page_dom.get("inputs", [])),
        "buttons": [b["text"] for b in page_dom.get("buttons", []) if b.get("text")][:15],
        "navigation_links": page_dom.get("navigation", [])[:10],
        "headings": page_dom.get("page_structure", {}).get("headings", {}),
        "form_methods": [f.get("method") for f in page_dom.get("forms", [])],
        "form_actions": [f.get("action") for f in page_dom.get("forms", [])],
        "input_types": list({i.get("type") for i in page_dom.get("inputs", []) if i.get("type")}),
        "input_names": [i.get("name") or i.get("id") for i in page_dom.get("inputs", []) if i.get("name") or i.get("id")][:20],
    }

    prompt = LAYER1_PROMPT.format(dom_data=json.dumps(compact_dom, indent=2))

    result = call_ollama_json(prompt, system=LAYER1_SYSTEM)

    if not result:
        logger.warning(f"[Layer 1] Empty result for {page_dom.get('url')}. Using fallback.")
        result = _fallback_understanding(page_dom)

    result["_raw_url"] = page_dom.get("url")
    logger.info(f"[Layer 1] ✓ Page type: {result.get('page_type')} | Score: {result.get('testability_score')}")
    return result


def analyse_all_pages(dom_data: list[dict]) -> list[dict]:
    """Run Layer 1 analysis on all crawled pages."""
    logger.info(f"[Layer 1] Analysing {len(dom_data)} pages...")
    analyses = []
    for page in dom_data:
        try:
            analysis = analyse_page(page)
            analyses.append(analysis)
        except Exception as e:
            logger.error(f"[Layer 1] Failed on {page.get('url')}: {e}")
            analyses.append(_fallback_understanding(page))

    # Save
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.PAGE_ANALYSIS_PATH, "w") as f:
        json.dump(analyses, f, indent=2)
    logger.info(f"[Layer 1] ✓ Page analyses saved to {config.PAGE_ANALYSIS_PATH}")
    return analyses


def _fallback_understanding(page_dom: dict) -> dict:
    """Minimal fallback when AI fails."""
    has_login  = any(i.get("type") == "password" for i in page_dom.get("inputs", []))
    has_forms  = len(page_dom.get("forms", [])) > 0
    page_type  = "login" if has_login else ("form" if has_forms else "other")
    return {
        "url": page_dom.get("url"),
        "page_type": page_type,
        "page_purpose": f"Page at {page_dom.get('url')}",
        "primary_actions": [],
        "user_journeys": [],
        "critical_elements": [],
        "risk_areas": [],
        "testability_score": 5,
        "notes": "Fallback analysis — AI layer did not return a valid response.",
    }
