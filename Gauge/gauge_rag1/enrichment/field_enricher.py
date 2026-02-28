# ===== enrichment/field_enricher.py =====

import json
import re
from pathlib import Path

# -------------------------------------------------
# PATH CONFIG
# -------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "elements.json"
OUTPUT_FILE = DATA_DIR / "enriched_elements.json"


# -------------------------------------------------
# SEMANTIC KEYWORDS (Boundary Safe)
# -------------------------------------------------

SEMANTIC_RULES = {
    "loan_amount": ["loan amount", "principal"],
    "down_payment": ["down payment"],
    "interest_rate": ["interest rate", "apr"],
    "duration": ["years", "months", "term", "duration"],
    "emi": ["emi", "monthly payment"],
    "salary": ["salary", "wages", "compensation"],
    "tax": ["tax", "withheld"],
    "price": ["price", "cost"],
    "percentage": ["percent", "%", "rate"],
    "capital_gain": ["capital gain"],
    "dividend": ["dividend"],
    "income": ["income"],
    "deduction": ["deduction", "donation", "interest"],
    "email": ["email"],
    "password": ["password"],
    "username": ["username", "user id", "login"],
    "phone": ["phone", "mobile"],
    "otp": ["otp", "verification"],
    "date": ["date", "dob", "birth"],
    "year": ["year"],
    "month": ["month", "jan", "feb", "mar"],
    "age": ["age"],
    "weight": ["weight"],
    "height": ["height"],
    "search": ["search"]
}


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def normalize(text):
    if not text:
        return ""
    return str(text).lower().strip()


def safe_get(field, key):
    value = field.get(key)
    if value is None:
        return ""
    return str(value)


def keyword_match(keyword, text):
    """
    Word-boundary safe matching.
    Prevents false positives like:
    'term' inside 'searchTerm'
    """
    return re.search(rf"\b{re.escape(keyword)}\b", text)


# -------------------------------------------------
# SEMANTIC DETECTION
# -------------------------------------------------

def detect_semantic(field):

    combined = " ".join([
        safe_get(field, "label"),
        safe_get(field, "name"),
        safe_get(field, "id"),
        safe_get(field, "placeholder")
    ])

    combined = normalize(combined)
    html_type = normalize(safe_get(field, "type"))

    # HTML type based detection
    if html_type == "email":
        return "email"

    if html_type == "password":
        return "password"

    if html_type == "date":
        return "date"

    if html_type == "number":
        return "numeric"

    # Numeric-like keywords
    if re.search(r"\b(amount|income|rate|tax|price|salary|gain|payment)\b", combined):
        return "numeric"

    # Keyword detection (boundary safe)
    for semantic, keywords in SEMANTIC_RULES.items():
        for keyword in keywords:
            if keyword_match(keyword, combined):
                return semantic

    return "generic_text"


# -------------------------------------------------
# COMPLEXITY SCORING
# -------------------------------------------------

def calculate_complexity(field):

    semantic = field.get("semantic_type", "")
    html_type = normalize(safe_get(field, "type"))
    options = field.get("options", [])

    score = 1  # base

    # Authentication fields
    if semantic in ["password", "email"]:
        score += 4

    # High-risk financial
    elif semantic in ["loan_amount", "tax", "interest_rate"]:
        score += 3

    # Medium-risk numeric
    elif semantic in ["numeric", "salary", "income", "price", "capital_gain", "percentage"]:
        score += 2

    # Dropdown complexity
    if options:
        if len(options) > 50:
            score += 3
        elif len(options) > 10:
            score += 2
        else:
            score += 1

    # Checkbox minor complexity
    if html_type == "checkbox":
        score += 1

    return score


# -------------------------------------------------
# ENRICH FUNCTION
# -------------------------------------------------

def enrich():

    if not INPUT_FILE.exists():
        print("❌ elements.json not found")
        return

    pages = json.loads(INPUT_FILE.read_text(encoding="utf-8"))

    for page in pages:
        for form in page.get("forms", []):
            for field in form.get("fields", []):

                # Safe fallback label (prevents empty labels)
                field["label"] = (
                    safe_get(field, "label")
                    or safe_get(field, "name")
                    or safe_get(field, "id")
                )

                # Semantic detection
                field["semantic_type"] = detect_semantic(field)

                # Complexity scoring
                field["complexity_score"] = calculate_complexity(field)

    OUTPUT_FILE.write_text(
        json.dumps(pages, indent=2),
        encoding="utf-8"
    )

    print("✅ enriched_elements.json generated successfully")


# -------------------------------------------------
# ENTRY
# -------------------------------------------------

if __name__ == "__main__":
    enrich()
