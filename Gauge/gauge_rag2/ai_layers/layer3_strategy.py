# ai_layers/layer3_strategy.py - AI Layer 3: Test Strategy Generation

import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ai_layers.ai_utils import call_ollama_json
from ai_layers.prompt_templates import LAYER3_SYSTEM, LAYER3_PROMPT, RAG_CONTEXT_TEMPLATE

logger = logging.getLogger(__name__)


def generate_strategy(page_understanding: dict, field_analysis: dict, rag_context: str = "") -> dict:
    """
    Layer 3: Synthesises Layer 1 + Layer 2 outputs and RAG context into
    a complete, prioritised test strategy with Gauge-ready scenarios.
    """
    url = page_understanding.get("url", page_understanding.get("_raw_url", "unknown"))
    logger.info(f"[Layer 3] Generating test strategy for: {url}")

    rag_section = RAG_CONTEXT_TEMPLATE.format(retrieved_chunks=rag_context) if rag_context else "No prior context available."

    prompt = LAYER3_PROMPT.format(
        page_understanding=json.dumps(page_understanding, indent=2),
        field_analysis=json.dumps(field_analysis, indent=2),
        rag_context=rag_section,
    )

    result = call_ollama_json(prompt, system=LAYER3_SYSTEM)

    if not result or "test_scenarios" not in result:
        logger.warning(f"[Layer 3] Empty/invalid strategy for {url}. Using fallback.")
        result = _fallback_strategy(page_understanding, field_analysis)

    result["url"] = url
    scenario_count = len(result.get("test_scenarios", []))
    logger.info(f"[Layer 3] ✓ {scenario_count} scenarios generated for {url}")
    return result


def generate_all_strategies(
    page_analyses: list[dict],
    field_analyses: list[dict],
    retriever=None,
) -> list[dict]:
    """Run Layer 3 for all pages."""
    logger.info(f"[Layer 3] Generating strategies for {len(page_analyses)} pages...")

    # Build lookup by URL
    field_map = {f.get("url", ""): f for f in field_analyses}

    strategies = []
    for pa in page_analyses:
        url = pa.get("url", pa.get("_raw_url", ""))
        fa  = field_map.get(url, {"url": url, "forms": []})

        # Fetch RAG context if retriever is available
        rag_context = ""
        if retriever:
            try:
                query = f"{pa.get('page_type', '')} {pa.get('page_purpose', '')} {url}"
                chunks = retriever.retrieve(query)
                rag_context = "\n\n".join(chunks)
            except Exception as e:
                logger.warning(f"[Layer 3] RAG retrieval failed: {e}")

        try:
            strategy = generate_strategy(pa, fa, rag_context)
            strategies.append(strategy)
        except Exception as e:
            logger.error(f"[Layer 3] Strategy generation failed for {url}: {e}")
            strategies.append({"url": url, "test_scenarios": [], "error": str(e)})

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.TEST_STRATEGY_PATH, "w") as f:
        json.dump(strategies, f, indent=2)
    logger.info(f"[Layer 3] ✓ Strategies saved to {config.TEST_STRATEGY_PATH}")
    return strategies


def _fallback_strategy(page_understanding: dict, field_analysis: dict) -> dict:
    """Generate minimal test strategy without AI."""
    url        = page_understanding.get("url", "")
    page_type  = page_understanding.get("page_type", "other")
    scenarios  = []

    # Happy path scenario
    scenarios.append({
        "scenario_id": "TC_001",
        "title": f"Verify {page_type} page loads successfully",
        "category": "functional",
        "priority": "high",
        "preconditions": ["Browser is open"],
        "steps": [
            {"action": "navigate", "target": url, "value": "", "description": f"Navigate to {url}"},
            {"action": "verify", "target": "body", "value": "page loaded", "description": "Verify page loads"},
        ],
        "expected_result": "Page loads without errors",
        "tags": ["smoke", "functional"],
    })

    # Add form submission scenario if forms exist
    for form in field_analysis.get("forms", []):
        scenarios.append({
            "scenario_id": f"TC_{len(scenarios)+1:03d}",
            "title": f"Submit {form.get('form_purpose', 'form')} with valid data",
            "category": "functional",
            "priority": "high",
            "preconditions": ["User is on the correct page"],
            "steps": [
                {"action": "navigate", "target": url, "value": "", "description": "Navigate to page"},
                {"action": "verify", "target": "form", "value": "form visible", "description": "Form is visible"},
            ],
            "expected_result": "Form submits successfully",
            "tags": ["functional", "form"],
        })

    return {
        "url": url,
        "page_type": page_type,
        "priority": "medium",
        "test_scenarios": scenarios,
        "test_data_table": {"description": "", "headers": [], "rows": []},
    }
