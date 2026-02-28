# ===== ai_layers/layer1_page_understanding.py =====

import json
import re
import requests
from pathlib import Path


# -------------------------------------------------
# PATHS
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "enriched_elements.json"
OUTPUT_FILE = DATA_DIR / "page_analysis.json"


# -------------------------------------------------
# OLLAMA CONFIG
# -------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"   # ensure this exists via `ollama list`


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
# LLM CALL
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
                    "temperature": 0.1
                }
            },
            timeout=120
        )

        response.raise_for_status()
        return response.json().get("response", "")

    except Exception as e:
        print("❌ Ollama call failed:", e)
        return ""


# -------------------------------------------------
# PROMPT BUILDER (Improved Taxonomy)
# -------------------------------------------------

def build_prompt(page):

    field_summary = []

    for form in page.get("forms", []):
        for field in form.get("fields", []):
            field_summary.append({
                "label": field.get("label"),
                "semantic_type": field.get("semantic_type"),
                "complexity_score": field.get("complexity_score")
            })

    return f"""
You are a senior QA automation engineer.

Classify this page.

IMPORTANT RULES:

- If password field AND title contains "sign in" or "login" → login
- If password field AND title contains "register" or "create account" → account_creation
- If finance-related (loan, interest, tax, investment, mortgage) → financial_calculator
- If math-related (gpa, triangle, algebra, geometry) → math_calculator
- If utility-related (age, subnet, unit conversion) → utility_calculator
- If only one simple text input → search
- If mostly content and no real form → informational

Return STRICT JSON only.

Format:

{{
  "page_type": "login | account_creation | financial_calculator | math_calculator | utility_calculator | search | informational | generic_form",
  "risk_level": "low | medium | high",
  "confidence": 0.0,
  "reasoning": "short reasoning"
}}

Page Title:
{page.get("title")}

URL:
{page.get("page_url")}

Fields:
{json.dumps(field_summary, indent=2)}
"""


# -------------------------------------------------
# DETERMINISTIC OVERRIDE (Hybrid Intelligence)
# -------------------------------------------------

def apply_rules(parsed, page):

    title = page.get("title", "").lower()

    # Login override
    if "sign in" in title or "login" in title:
        parsed["page_type"] = "login"
        parsed["risk_level"] = "high"
        parsed["reasoning"] = "login page detected from title"
        return parsed

    # Register override
    if "register" in title or "create account" in title:
        parsed["page_type"] = "account_creation"
        parsed["risk_level"] = "high"
        parsed["reasoning"] = "account creation detected from title"
        return parsed

    return parsed


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def run_layer1():

    if not INPUT_FILE.exists():
        print("❌ enriched_elements.json not found")
        return

    pages = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    results = []

    for page in pages:

        if not page.get("forms"):
            continue

        print(f"🧠 Analyzing page: {page.get('title')}")

        prompt = build_prompt(page)
        response = ask_llm(prompt)

        parsed = extract_json(response)

        if not parsed:
            print("⚠ Could not parse model output")
            print("Raw response:\n", response)
            continue

        parsed = apply_rules(parsed, page)
        parsed["url"] = page.get("page_url")

        results.append(parsed)

    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8"
    )

    print("✅ page_analysis.json generated successfully")


if __name__ == "__main__":
    run_layer1()
