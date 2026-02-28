import json
import random
from pathlib import Path

# -------------------------------------------------
# PATH CONFIG
# -------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
KB_DIR = BASE_DIR / "knowledge_base"

FINANCIAL_FILE = KB_DIR / "financial_rules.json"
LOGIN_FILE = KB_DIR / "login_rules.json"
BOUNDARY_FILE = KB_DIR / "boundary_rules.json"


# -------------------------------------------------
# SAFE LOAD
# -------------------------------------------------

def safe_load(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return {}


FINANCIAL = safe_load(FINANCIAL_FILE)
LOGIN = safe_load(LOGIN_FILE)
BOUNDARY = safe_load(BOUNDARY_FILE)


# -------------------------------------------------
# MERGE ALL KNOWLEDGE
# -------------------------------------------------

KNOWLEDGE = {}
KNOWLEDGE.update(FINANCIAL)
KNOWLEDGE.update(LOGIN)
KNOWLEDGE.update(BOUNDARY)


# -------------------------------------------------
# VALUE RETRIEVAL
# -------------------------------------------------

def get_values(semantic_type, scenario_type="positive"):
    """
    semantic_type: loan_amount, interest_rate, email etc
    scenario_type: positive | boundary | invalid
    """

    if semantic_type not in KNOWLEDGE:
        return ["sample"]

    rule = KNOWLEDGE[semantic_type]

    if scenario_type in rule:
        values = rule[scenario_type]
        if isinstance(values, list):
            return values

    # fallback order
    for fallback in ["positive", "boundary", "invalid"]:
        if fallback in rule:
            return rule[fallback]

    return ["sample"]


# -------------------------------------------------
# SINGLE VALUE HELPER
# -------------------------------------------------

def get_single_value(semantic_type, scenario_type="positive"):
    values = get_values(semantic_type, scenario_type)
    return str(random.choice(values))


# -------------------------------------------------
# TEST
# -------------------------------------------------

if __name__ == "__main__":
    print("Loan positive:", get_values("loan_amount", "positive"))
    print("Interest invalid:", get_values("interest_rate", "invalid"))
    print("Email boundary:", get_values("email", "invalid"))
