# ===== ai_layers/layer3_strategy.py =====

import json
import re
import requests
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

PAGE_ANALYSIS_FILE = DATA_DIR / "page_analysis.json"
FIELD_ANALYSIS_FILE = DATA_DIR / "field_analysis.json"
OUTPUT_FILE = DATA_DIR / "test_strategy.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"   # IMPORTANT: use mistral (faster)


# -------------------------------------------------
# SAFE JSON EXTRACTOR
# -------------------------------------------------

def extract_json(text):
    try:
        return json.loads(text)
    except:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            return None
    return None


# -------------------------------------------------
# LLM CALL (FAST)
# -------------------------------------------------

def ask_llm(prompt):

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 300   # VERY IMPORTANT
                }
            },
            timeout=60
        )

        response.raise_for_status()
        return response.json().get("response", "")

    except Exception as e:
        print("⚠ LLM failed:", e)
        return ""


# -------------------------------------------------
# BASE STRATEGY (DETERMINISTIC FOUNDATION)
# -------------------------------------------------

def base_strategy(page_type, field_data):

    strategy = {
        "test_scenarios": [{"name": "Basic Validation"}],
        "boundary_tests": [],
        "negative_tests": [],
        "relationship_tests": [],
        "risk_based_tests": [],
        "priority": "medium"
    }

    if page_type == "login":
        strategy["priority"] = "high"

    return strategy


# -------------------------------------------------
# AI ENHANCEMENT PROMPT (SMALL CONTEXT)
# -------------------------------------------------

def build_prompt(page_type, field_data):

    summary = {
        "page_type": page_type,
        "critical_fields": field_data.get("critical_fields", []),
        "derived_fields": field_data.get("derived_fields", [])
    }

    return f"""
Enhance QA test strategy.

Return STRICT JSON only:

{{
  "extra_boundary_tests": [],
  "extra_negative_tests": [],
  "extra_risk_tests": []
}}

Context:
{json.dumps(summary, indent=2)}
"""


# -------------------------------------------------
# MERGE AI OUTPUT
# -------------------------------------------------

def merge_strategy(base, ai_output):

    if not isinstance(ai_output, dict):
        return base

    for item in ai_output.get("extra_boundary_tests", []):
        base["boundary_tests"].append(item)

    for item in ai_output.get("extra_negative_tests", []):
        base["negative_tests"].append(item)

    for item in ai_output.get("extra_risk_tests", []):
        base["risk_based_tests"].append(item)

    return base


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def run_layer3():

    if not PAGE_ANALYSIS_FILE.exists() or not FIELD_ANALYSIS_FILE.exists():
        print("❌ Required input files missing")
        return

    page_analysis = json.loads(PAGE_ANALYSIS_FILE.read_text(encoding="utf-8"))
    field_analysis = json.loads(FIELD_ANALYSIS_FILE.read_text(encoding="utf-8"))

    page_type_map = {p["url"]: p["page_type"] for p in page_analysis}

    results = []

    for field_page in field_analysis:

        url = field_page["url"]
        page_type = page_type_map.get(url, "generic_form")

        print(f"🧠 Generating strategy: {url}")

        base = base_strategy(page_type, field_page)

        prompt = build_prompt(page_type, field_page)
        response = ask_llm(prompt)

        parsed = extract_json(response)

        final_strategy = merge_strategy(base, parsed)
        final_strategy["url"] = url

        results.append(final_strategy)

    OUTPUT_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("✅ test_strategy.json generated successfully")


if __name__ == "__main__":
    run_layer3()