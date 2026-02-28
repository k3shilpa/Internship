import sys
import json
from pathlib import Path

# -------------------------------------------------
# FIX IMPORT PATH (VERY IMPORTANT)
# -------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from rag.retriever import get_single_value

# -------------------------------------------------
# PATHS
# -------------------------------------------------

DATA_DIR = BASE_DIR / "data"

ENRICHED_FILE = DATA_DIR / "enriched_elements.json"
STRATEGY_FILE = DATA_DIR / "test_strategy.json"
OUTPUT_FILE = DATA_DIR / "test_plan.json"


# -------------------------------------------------
# SAFE LOAD
# -------------------------------------------------

def load_json(path):
    if not path.exists():
        print(f"❌ Missing file: {path.name}")
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Failed to load {path.name}: {e}")
        return []


# -------------------------------------------------
# MAIN BUILDER
# -------------------------------------------------

def build_tests():

    enriched_pages = load_json(ENRICHED_FILE)
    strategies = load_json(STRATEGY_FILE)

    if not enriched_pages or not strategies:
        print("⚠ Missing enriched data or strategy.")
        return

    page_map = {page["page_url"]: page for page in enriched_pages}
    final_scenarios = []
    scenario_counter = {}

    for strategy in strategies:

        url = strategy.get("url")
        page = page_map.get(url)

        if not page:
            continue

        for scenario in strategy.get("test_matrix", []):

            scenario_name = scenario.get("scenario_name", "Scenario")
            scenario_type = scenario.get("scenario_type", "positive")
            field_focus = scenario.get("field_focus", [])

            # Avoid duplicate scenario names
            scenario_counter[scenario_name] = scenario_counter.get(scenario_name, 0) + 1
            if scenario_counter[scenario_name] > 1:
                scenario_name = f"{scenario_name} ({scenario_counter[scenario_name]})"

            steps = []

            # Navigate first
            steps.append({
                "action": "navigate",
                "url": url
            })

            for form in page.get("forms", []):

                # Fill fields
                for field in form.get("fields", []):

                    semantic_type = field.get("semantic_type")
                    xpath = field.get("xpath")

                    if not xpath:
                        continue

                    if semantic_type in field_focus:
                        value = get_single_value(semantic_type, scenario_type)
                    else:
                        value = get_single_value(semantic_type, "positive")

                    steps.append({
                        "action": "enter",
                        "xpath": xpath,
                        "value": str(value)
                    })

                # Click first submit button
                for btn in form.get("submit_buttons", []):
                    if btn.get("xpath"):
                        steps.append({
                            "action": "click",
                            "xpath": btn["xpath"]
                        })
                        break

            if len(steps) > 1:
                final_scenarios.append({
                    "scenario": scenario_name,
                    "steps": steps
                })

    OUTPUT_FILE.write_text(
        json.dumps(final_scenarios, indent=2),
        encoding="utf-8"
    )

    print("✅ test_plan.json generated successfully")


# -------------------------------------------------
# ENTRY
# -------------------------------------------------

if __name__ == "__main__":
    build_tests()
