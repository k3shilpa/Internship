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
    "You are an expert QA engineer specialising in exploratory web testing. "
    "Given a DOM analysis of a web page and relevant testing patterns, "
    "generate comprehensive exploratory test cases. "
    "Return ONLY a valid JSON array. Each element must have: "
    '{"title": "Short descriptive title", '
    '"category": "functional|navigation|form|accessibility|edge_case|security", '
    '"steps": ["Step 1 description", "Step 2 description"], '
    '"expected": "Expected result after all steps"} '
    "Be thorough. Cover happy paths, edge cases, error states, "
    "accessibility, and security basics. "
    "Return 8-15 test cases. No markdown, no prose - pure JSON array only."
)


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