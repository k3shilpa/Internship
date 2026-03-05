"""
testcase_generator.py
=====================
Sends DOM summary + RAG context to Groq LLaMA and parses structured test cases.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from groq import Groq

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in .env")
        _client = Groq(api_key=api_key)
    return _client


SYSTEM_PROMPT = (
    "You are a senior QA automation engineer. Your job is to generate executable Gauge test cases "
    "that map EXACTLY to pre-built Playwright step implementations.\n\n"

    "═══════════════════════════════════════════════════════\n"
    "AVAILABLE STEPS — you may ONLY use steps from this list\n"
    "═══════════════════════════════════════════════════════\n"
    "NAVIGATION:\n"
    "  Open browser and navigate to base URL\n"
    "  Navigate to <url>                         (e.g. Navigate to /about)\n"
    "  Refresh the page\n"
    "  Go back to previous page\n"
    "  Go forward to next page\n\n"

    "CLICKING:\n"
    "  Click button <label>                      (e.g. Click button Search)\n"
    "  Click link <label>                        (e.g. Click link Home)\n"
    "  Click on <element>                        (e.g. Click on logo)\n"
    "  Click on a navigation link\n"
    "  Click on forgot password link\n"
    "  Double click on <element>\n"
    "  Hover over <element>\n\n"

    "INPUT:\n"
    "  Enter <text> in <field>                   (e.g. Enter hello@test.com in email)\n"
    "  Type <text> in <field>\n"
    "  Clear field <field>\n"
    "  Select <option> from <dropdown>\n"
    "  Check checkbox <label>\n"
    "  Uncheck checkbox <label>\n"
    "  Press key <key>                           (e.g. Press key Enter)\n"
    "  Enter a sql injection string in the login form\n"
    "  Submit the form\n\n"

    "SCROLLING:\n"
    "  Scroll down\n"
    "  Scroll up\n"
    "  Scroll to <element>\n"
    "  Focus on <element>\n\n"

    "VERIFICATION:\n"
    "  Verify: <assertion>                       (e.g. Verify: error message is visible)\n"
    "  Verify page title contains <text>\n"
    "  Verify text <text> is visible\n"
    "  Verify text <text> is not visible\n"
    "  Verify element <sel> is visible\n"
    "  Verify current URL contains <path>\n\n"

    "WAITING:\n"
    "  Wait for network idle\n"
    "  Wait <seconds> seconds                    (e.g. Wait 2 seconds)\n"
    "  Wait for element <sel>\n\n"

    "AUTH:\n"
    "  Log in with username <username> and password <password>\n"
    "  Log out\n\n"

    "OTHER:\n"
    "  Take a screenshot\n"
    "  Perform action <description>              (last resort only — prefer specific steps above)\n\n"

    "═══════════════════════════════\n"
    "STEP WRITING RULES — MANDATORY\n"
    "═══════════════════════════════\n"
    "1. Every step must be COPIED EXACTLY from the list above, with <placeholders> replaced by real values.\n"
    "2. Use REAL, SPECIFIC values — not placeholders.\n"
    "   BAD : Enter <email> in email\n"
    "   GOOD: Enter test@example.com in email\n"
    "3. Each test case must start with: Open browser and navigate to base URL\n"
    "4. Every test case must end with at least one Verify step.\n"
    "5. Use 'Perform action' ONLY for things no other step covers (e.g. screen reader simulation).\n"
    "6. Steps must be ordered logically — set up state before asserting it.\n\n"

    "══════════════════════════════════\n"
    "COVERAGE — include ALL categories\n"
    "══════════════════════════════════\n"
    "functional  : core happy paths — primary user journeys that must work\n"
    "navigation  : links, back/forward, deep links, redirect behaviour\n"
    "form        : valid submit, required-field validation, format validation\n"
    "edge_case   : empty input, whitespace-only, 500+ char string, special chars (!@#$%^&*)\n"
    "negative    : wrong credentials, invalid formats, missing required fields\n"
    "security    : SQL injection via form, XSS probe in input fields, sensitive data in URL check\n"
    "accessibility: tab key navigation, keyboard-only form completion, visible focus states\n"
    "performance : behaviour with slow/throttled conditions, rapid repeated clicks\n\n"

    "═══════════════════════════\n"
    "EXPECTED RESULT RULES\n"
    "═══════════════════════════\n"
    "Must describe what the USER SEES — a visible, specific, on-screen outcome.\n"
    "BAD : 'System handles the request'\n"
    "GOOD: 'A red error banner appears with text \"Invalid email address\" below the email field'\n\n"

    "═══════════════\n"
    "OUTPUT FORMAT\n"
    "═══════════════\n"
    "Return ONLY a valid JSON array. No markdown. No prose. No explanation.\n"
    "[\n"
    "  {\n"
    '    "title": "Max 60 chars, action-oriented title",\n'
    '    "category": "functional|navigation|form|edge_case|negative|security|accessibility|performance",\n'
    '    "priority": "high|medium|low",\n'
    '    "steps": [\n'
    '      "Open browser and navigate to base URL",\n'
    '      "Enter test@example.com in email",\n'
    '      "Click button Submit",\n'
    '      "Verify: success message is displayed"\n'
    '    ],\n'
    '    "expected": "Specific visible outcome the user sees on screen"\n'
    "  }\n"
    "]\n\n"

    "Generate 15-20 test cases. Spread evenly across all 8 categories. "
    "Prioritise high and medium. No two test cases should test the same scenario.")


class TestCaseGenerator:
    """Generate test cases using Groq LLaMA."""

    def __init__(self):
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def generate(self, dom_data: dict[str, Any], rag_context: str) -> list[dict]:
        """Call Groq to produce test cases, return list of dicts."""
        user_message = self._build_prompt(dom_data, rag_context)

        response = _get_client().chat.completions.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
        )

        raw = response.choices[0].message.content.strip()
        return self._parse_response(raw)

    def _build_prompt(self, dom_data: dict, rag_context: str) -> str:
        forms_json   = json.dumps(dom_data.get("forms",   []), indent=2)[:2000]
        buttons_json = json.dumps(dom_data.get("buttons", []), indent=2)[:1000]

        parts = [
            "## DOM Analysis",
            dom_data.get("summary", ""),
            "",
            "## Forms Detail",
            forms_json,
            "",
            "## Buttons",
            buttons_json,
            "",
            "## Relevant Testing Patterns (RAG Context)",
            rag_context[:3000],
            "",
            "## Task",
            "Generate exploratory test cases for this web application.",
        ]
        return "\n".join(parts)

    def _parse_response(self, raw: str) -> list[dict]:
        # Strip markdown code fences if present
        clean = re.sub(r"```(?:json)?", "", raw).strip()
        clean = re.sub(r"```", "", clean).strip()

        # Find the JSON array boundaries
        start = clean.find("[")
        end   = clean.rfind("]")

        if start == -1 or end == -1:
            print("[TestCaseGenerator] WARNING: No JSON array found in response.")
            print("[TestCaseGenerator] Raw response:", raw[:300])
            return []

        try:
            cases  = json.loads(clean[start : end + 1])
            result = []
            for tc in cases:
                if not isinstance(tc, dict):
                    continue
                if "title" not in tc or "steps" not in tc:
                    continue
                result.append({
                    "title":    str(tc.get("title",    "Untitled")),
                    "category": str(tc.get("category", "exploratory")),
                    "steps":    [str(s) for s in tc.get("steps", [])],
                    "expected": str(tc.get("expected", "")),
                    "status":   None,
                })
            return result

        except json.JSONDecodeError as exc:
            print(f"[TestCaseGenerator] JSON parse error: {exc}")
            print("[TestCaseGenerator] Attempted to parse:", clean[start:end+1][:300])
            return []