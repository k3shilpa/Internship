# gauge_builder/strategy_normalizer.py
# Converts strategy_raw.json → strategy_normalized.json

import json
import os
import sys
import re
from pathlib import Path
import logging

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import config

logger = logging.getLogger(__name__)

RAW_PATH = os.path.join(config.DATA_DIR, "test_strategy.json")
NORMALIZED_PATH = os.path.join(config.DATA_DIR, "strategy_normalized.json")


# ==============================================================================
# STEP NORMALIZATION
# ==============================================================================

def normalize_step(step):
    """
    Convert step into clean string format.
    """

    # If already string
    if isinstance(step, str):
        step = step.strip()

        # Convert single quotes → double quotes
        step = step.replace("'", '"')

        # Add quotes if missing (for Navigate / Enter / Select)
        if step.startswith("Navigate to ") and '"' not in step:
            url = step.replace("Navigate to ", "").strip()
            return f'Navigate to "{url}"'

        if step.startswith("Enter ") and '"' not in step:
            parts = step.split(" ")
            field = " ".join(parts[1:-1])
            value = parts[-1]
            return f'Enter {field} "{value}"'

        if step.startswith("Select ") and '"' not in step:
            parts = step.split(" ")
            field = " ".join(parts[1:-1])
            value = parts[-1]
            return f'Select {field} "{value}"'

        return step

    # If step is dict (AI structured format)
    if isinstance(step, dict):

        action = step.get("action", "").lower()
        target = step.get("target", "")
        value = step.get("value", "")

        if action == "navigate":
            return f'Navigate to "{target}"'

        if action == "verify":
            return f'Verify the page contains "{value}"'

        if action == "enter":
            return f'Enter {target} "{value}"'

        # fallback
        description = step.get("description", "")
        return description.strip()

    return None


# ==============================================================================
# MAIN NORMALIZER
# ==============================================================================

def normalize_strategy(raw_data):

    normalized = []

    for module in raw_data:

        # Skip AI error blocks
        if module.get("error"):
            continue

        scenarios = module.get("test_scenarios", [])
        if not scenarios:
            continue

        clean_module = {
            "url": module.get("url"),
            "module_name": module.get("module_name", "MODULE"),
            "test_scenarios": []
        }

        for scenario in scenarios:

            steps = scenario.get("steps", [])
            clean_steps = []

            for step in steps:
                normalized_step = normalize_step(step)
                if normalized_step:
                    clean_steps.append(normalized_step)

            if not clean_steps:
                continue

            clean_scenario = {
                "scenario_id": scenario.get("scenario_id"),
                "title": scenario.get("title"),
                "steps": clean_steps
            }

            clean_module["test_scenarios"].append(clean_scenario)

        if clean_module["test_scenarios"]:
            normalized.append(clean_module)

    return normalized


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main():
    logging.basicConfig(level=logging.INFO)

    if not os.path.exists(RAW_PATH):
        print("strategy_raw.json not found.")
        sys.exit(1)

    with open(RAW_PATH, encoding="utf-8") as f:
        raw_data = json.load(f)

    normalized = normalize_strategy(raw_data)

    os.makedirs(os.path.dirname(NORMALIZED_PATH), exist_ok=True)

    with open(NORMALIZED_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2)

    print("✓ strategy_normalized.json created successfully.")


if __name__ == "__main__":
    main()