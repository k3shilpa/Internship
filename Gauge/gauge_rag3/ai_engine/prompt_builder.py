"""
ai_engine/prompt_builder.py
Builds Groq prompts.  Imported by test_generator.py — do not run directly.
"""
import json

SYSTEM_PROMPT = """You are a senior QA automation engineer with 10+ years of web testing experience.
Analyse the web page element data and generate comprehensive, realistic test cases.

COVER:
- Happy path: valid inputs, expected navigation flows
- Negative path: empty required fields, invalid formats, too long/short values
- Accessibility: images need alt text, inputs need labels
- Navigation: every link loads the correct page
- E-commerce: product display, add-to-cart, price visibility
- At least 1 negative test per form found

OUTPUT FORMAT — return ONLY valid JSON, no markdown, no text outside the JSON:
{
  "test_suite": "Suite name",
  "url": "page url",
  "page_type": "page type",
  "test_cases": [
    {
      "id": "TC_001",
      "name": "Short descriptive name",
      "category": "functional|navigation|form|ui|accessibility|e2e",
      "priority": "high|medium|low",
      "description": "What this test verifies",
      "preconditions": ["User is on the page"],
      "steps": [
        {
          "step_number": 1,
          "action": "navigate|click|type|verify|select|hover|wait|assert_text|assert_visible|assert_url|clear|scroll",
          "target": {
            "element_type": "button|input|link|select|form|page",
            "selector_type": "id|css|xpath|name",
            "selector_value": "exact-selector",
            "description": "human label"
          },
          "input_data": "text to enter, or null",
          "expected_result": "what should happen"
        }
      ],
      "expected_outcome": "Final state after all steps",
      "tags": ["smoke"]
    }
  ]
}"""


def build_prompt(page_data: dict, rag_context: str = "") -> tuple:
    compressed = _compress(page_data)
    rag_block  = (
        "\nRELEVANT CONTEXT FROM KNOWLEDGE BASE:\n" + rag_context + "\n--- END CONTEXT ---\n"
    ) if rag_context.strip() else ""

    user_prompt = (
        f"Generate comprehensive test cases for this page.\n\n"
        f"URL: {page_data.get('url','unknown')}\n"
        f"Title: {page_data.get('title','unknown')}\n"
        f"Type: {page_data.get('page_type','general')}\n"
        f"{rag_block}\n"
        f"ELEMENTS:\n{json.dumps(compressed, indent=2)}\n\n"
        f"Return ONLY the JSON object."
    )

    words = user_prompt.split()
    if len(words) > 2200:
        user_prompt = " ".join(words[:2200]) + "\n\n[TRUNCATED] Generate test cases from above only."

    return SYSTEM_PROMPT, user_prompt


def _compress(page_data: dict) -> dict:
    e = page_data.get("elements", {})

    buttons = [{"text": el.get("text","")[:50], "selector": el.get("selector"), "disabled": el.get("disabled",False)}
               for el in e.get("interactive",[])[:20]]

    forms = []
    for form in e.get("forms",[])[:5]:
        slim = {"action": form.get("action",""), "method": form.get("method","GET"),
                "selector": form.get("selector"), "fields": [], "submit": form.get("submit_buttons",[])}
        for f in form.get("fields",[])[:15]:
            slim["fields"].append({"type": f.get("element_type"), "name": f.get("name",""),
                "placeholder": f.get("placeholder",""), "required": f.get("required",False),
                "label": f.get("label",""), "selector": f.get("selector"),
                "validation": {k:v for k,v in f.get("validation",{}).items() if v}})
        forms.append(slim)

    seen, links = set(), []
    for link in e.get("navigation",[]):
        text = link.get("text","").strip()
        if text and text not in seen and not link.get("is_external"):
            seen.add(text)
            links.append({"text": text[:40], "href": link.get("href","")[:80], "selector": link.get("selector")})
        if len(links) >= 12: break

    return {
        "buttons":       buttons,
        "forms":         forms,
        "links":         links,
        "tables":        [{"headers": t.get("headers",[]),"rows": t.get("row_count",0),"selector": t.get("selector")} for t in e.get("tables",[])[:3]],
        "images_no_alt": [{"selector": img.get("selector"),"src": img.get("src","")[:50]} for img in e.get("media",[]) if not img.get("has_alt",True)],
        "headings":      [{"level": h.get("level"),"text": h.get("text","")[:60]} for h in e.get("content",[])[:8]],
    }