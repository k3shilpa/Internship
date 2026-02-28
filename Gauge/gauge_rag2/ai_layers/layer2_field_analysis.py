# ai_layers/layer2_field_analysis.py - AI Layer 2: Field & Form Analysis

import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ai_layers.ai_utils import call_ollama_json
from ai_layers.prompt_templates import LAYER2_SYSTEM, LAYER2_PROMPT

logger = logging.getLogger(__name__)


def analyse_fields(page_dom: dict, page_understanding: dict) -> dict:
    """
    Layer 2: Takes DOM data + Layer 1 understanding and produces a detailed
    field-level analysis including test data, validation rules, and scenarios.
    """
    url = page_dom.get("url", "unknown")
    logger.info(f"[Layer 2] Analysing fields for: {url}")

    # Skip pages with no forms/inputs
    if not page_dom.get("forms") and not page_dom.get("inputs"):
        logger.info(f"[Layer 2] No forms/inputs on {url}, skipping.")
        return {"url": url, "forms": [], "skipped": True}

    # Compact field data for prompt
    fields_data = {
        "forms": page_dom.get("forms", []),
        "standalone_inputs": [
            i for i in page_dom.get("inputs", [])
            if i.get("visible") and i.get("type") not in ("hidden", "submit")
        ][:30],
    }

    prompt = LAYER2_PROMPT.format(
        page_understanding=json.dumps(page_understanding, indent=2),
        fields_data=json.dumps(fields_data, indent=2),
    )

    result = call_ollama_json(prompt, system=LAYER2_SYSTEM)

    if not result or "forms" not in result:
        logger.warning(f"[Layer 2] Empty/invalid result for {url}. Using fallback.")
        result = _fallback_field_analysis(page_dom, page_understanding)

    result["url"] = url
    logger.info(f"[Layer 2] ✓ {len(result.get('forms', []))} form(s) analysed for {url}")
    return result


def analyse_all_fields(dom_data: list[dict], page_analyses: list[dict]) -> list[dict]:
    """Run Layer 2 on all pages that have forms."""
    logger.info(f"[Layer 2] Running field analysis on {len(dom_data)} pages...")

    # Build lookup by URL
    understanding_map = {p.get("url", p.get("_raw_url", "")): p for p in page_analyses}

    results = []
    for page in dom_data:
        url = page.get("url", "")
        understanding = understanding_map.get(url, {})
        try:
            analysis = analyse_fields(page, understanding)
            results.append(analysis)
        except Exception as e:
            logger.error(f"[Layer 2] Failed on {url}: {e}")
            results.append({"url": url, "forms": [], "error": str(e)})

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.FIELD_ANALYSIS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"[Layer 2] ✓ Field analyses saved to {config.FIELD_ANALYSIS_PATH}")
    return results


def _fallback_field_analysis(page_dom: dict, understanding: dict) -> dict:
    """Generate a basic field analysis without AI."""
    forms = []
    for i, form in enumerate(page_dom.get("forms", [])):
        fields = []
        for field in form.get("fields", []):
            ftype = field.get("type", "text")
            fields.append({
                "name": field.get("name") or field.get("id") or f"field_{i}",
                "type": ftype,
                "label": field.get("label") or field.get("placeholder") or "",
                "required": field.get("required", False),
                "validation_rules": _infer_validation(field),
                "test_data": _default_test_data(ftype),
                "risk_level": "medium",
            })
        forms.append({
            "form_id": form.get("id") or str(i),
            "form_purpose": understanding.get("page_purpose", "Unknown form"),
            "fields": fields,
            "submission_scenarios": [],
        })
    return {"forms": forms}


def _infer_validation(field: dict) -> list:
    rules = []
    if field.get("required"):
        rules.append("required")
    if field.get("type") == "email":
        rules.append("must be valid email format")
    if field.get("type") == "number":
        rules.append("must be numeric")
    if field.get("maxlength"):
        rules.append(f"max length: {field['maxlength']}")
    if field.get("pattern"):
        rules.append(f"pattern: {field['pattern']}")
    return rules


def _default_test_data(field_type: str) -> dict:
    defaults = {
        "email":    {"valid": ["test@example.com", "user@domain.org"], "invalid": ["notanemail", "@nodomain"], "boundary": ["a@b.co"], "empty": "validation error"},
        "password": {"valid": ["Password123!", "SecureP@ss1"], "invalid": ["123", "abc"], "boundary": ["A1!aaaaa"], "empty": "validation error"},
        "text":     {"valid": ["John Doe", "Test User"], "invalid": [], "boundary": ["A", "x" * 255], "empty": "validation error if required"},
        "number":   {"valid": ["42", "100"], "invalid": ["abc", "-1"], "boundary": ["0", "999999"], "empty": "validation error if required"},
        "tel":      {"valid": ["+1234567890", "0123456789"], "invalid": ["abc", "123"], "boundary": ["0000000000"], "empty": "validation error if required"},
    }
    return defaults.get(field_type, {"valid": ["test_value"], "invalid": [], "boundary": [], "empty": "empty"})
