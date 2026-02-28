# ===== ai_layers/layer2_field_analysis.py =====

import json
import re
import requests
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

ENRICHED_FILE = DATA_DIR / "enriched_elements.json"
PAGE_ANALYSIS_FILE = DATA_DIR / "page_analysis.json"
OUTPUT_FILE = DATA_DIR / "field_analysis.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3:latest"


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
                "options": {"temperature": 0.1}
            },
            timeout=250
        )

        response.raise_for_status()
        return response.json().get("response", "")

    except Exception as e:
        print("❌ LLM call failed:", e)
        return ""


# -------------------------------------------------
# GENERIC FIELD FILTERING
# -------------------------------------------------

def filter_relevant_fields(page):
    filtered = []

    for form in page.get("forms", []):
        for field in form.get("fields", []):

            name = (field.get("name") or "").lower()
            label = (field.get("label") or "").strip()

            # Ignore global site search
            if name == "calcsearchterm":
                continue

            # Ignore empty labels
            if not label:
                continue

            filtered.append(field)

    return filtered


# -------------------------------------------------
# DETERMINISTIC STRUCTURAL INFERENCE (GENERIC)
# -------------------------------------------------

def generate_structural_rules(fields):

    logical_constraints = []
    critical_fields = []
    derived_fields = []
    field_relationships = []

    numeric_fields = []

    for f in fields:

        name = f.get("label") or f.get("name")
        semantic = f.get("semantic_type")
        html_type = (f.get("type") or "").lower()

        # Authentication
        if semantic in ["email", "password", "username"]:
            critical_fields.append(name)

        # Numeric
        if semantic in [
            "numeric", "loan_amount", "price",
            "salary", "income", "interest_rate", "duration"
        ]:
            numeric_fields.append(name)
            critical_fields.append(name)

            logical_constraints.append({
                "field": name,
                "rule": "must be numeric"
            })

        # Email
        if semantic == "email":
            logical_constraints.append({
                "field": name,
                "rule": "must match email format"
            })

        # Date
        if semantic == "date" or html_type == "date":
            critical_fields.append(name)
            logical_constraints.append({
                "field": name,
                "rule": "must be valid date"
            })

        # Dropdown
        if f.get("options"):
            logical_constraints.append({
                "field": name,
                "rule": "value must be one of allowed options"
            })

    # Generic calculation inference
    if len(numeric_fields) >= 2:
        derived_fields.append("Calculated Output")

        for nf in numeric_fields:
            field_relationships.append({
                "from": nf,
                "to": "Calculated Output",
                "relationship": "calculated_from"
            })

    return {
        "critical_fields": list(set(critical_fields)),
        "field_relationships": field_relationships,
        "logical_constraints": logical_constraints,
        "derived_fields": derived_fields
    }


# -------------------------------------------------
# LLM REFINEMENT LAYER (OPTIONAL)
# -------------------------------------------------

def build_prompt(page, page_type, fields):

    field_summary = [
        {
            "name": f.get("label"),
            "semantic_type": f.get("semantic_type")
        }
        for f in fields
    ]

    return f"""
You are a QA automation expert.

Refine structural field analysis.
Do NOT invent new fields.
Only improve relationships if clearly supported by provided fields.

Return STRICT JSON only:

{{
  "critical_fields": [],
  "field_relationships": [],
  "logical_constraints": [],
  "derived_fields": []
}}

Page Type: {page_type}

Fields:
{json.dumps(field_summary, indent=2)}
"""


# -------------------------------------------------
# SAFE MERGE FUNCTION
# -------------------------------------------------

def safe_merge(structural_output, parsed):

    if not isinstance(parsed, dict):
        return structural_output

    # ---- SAFE critical_fields ----
    ai_critical = parsed.get("critical_fields", [])
    clean_ai_critical = []

    if isinstance(ai_critical, list):
        for item in ai_critical:
            if isinstance(item, str):
                clean_ai_critical.append(item)
            elif isinstance(item, dict):
                field_name = item.get("field")
                if field_name and isinstance(field_name, str):
                    clean_ai_critical.append(field_name)

    structural_output["critical_fields"] = list(
        set(structural_output["critical_fields"] + clean_ai_critical)
    )

    # ---- SAFE field_relationships ----
    ai_relationships = parsed.get("field_relationships", [])
    if isinstance(ai_relationships, list):
        structural_output["field_relationships"] += [
            r for r in ai_relationships if isinstance(r, dict)
        ]

    # ---- SAFE logical_constraints ----
    ai_constraints = parsed.get("logical_constraints", [])
    if isinstance(ai_constraints, list):
        structural_output["logical_constraints"] += [
            c for c in ai_constraints if isinstance(c, dict)
        ]

    # ---- SAFE derived_fields ----
    ai_derived = parsed.get("derived_fields", [])
    if isinstance(ai_derived, list):
        structural_output["derived_fields"] += [
            d for d in ai_derived if isinstance(d, str)
        ]

    # Deduplicate
    structural_output["derived_fields"] = list(set(structural_output["derived_fields"]))

    return structural_output


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def run_layer2():

    if not ENRICHED_FILE.exists() or not PAGE_ANALYSIS_FILE.exists():
        print("❌ Required input files missing")
        return

    pages = json.loads(ENRICHED_FILE.read_text(encoding="utf-8"))
    page_analysis = json.loads(PAGE_ANALYSIS_FILE.read_text(encoding="utf-8"))

    page_type_map = {p["url"]: p["page_type"] for p in page_analysis}

    results = []

    for page in pages:

        if not page.get("forms"):
            continue

        url = page["page_url"]
        page_type = page_type_map.get(url, "generic_form")

        print(f"🔍 Field analysis: {page['title']}")

        relevant_fields = filter_relevant_fields(page)

        if not relevant_fields:
            continue

        # Step 1: Deterministic structural inference
        structural_output = generate_structural_rules(relevant_fields)

        # Step 2: Optional AI refinement
        prompt = build_prompt(page, page_type, relevant_fields)
        response = ask_llm(prompt)

        parsed = extract_json(response)

        # Step 3: Safe merge
        structural_output = safe_merge(structural_output, parsed)

        structural_output["url"] = url
        results.append(structural_output)

    OUTPUT_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("✅ field_analysis.json generated successfully")


if __name__ == "__main__":
    run_layer2()
