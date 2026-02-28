# ai_layers/prompt_templates.py - Centralised prompt templates

# ─── Layer 1: Page Understanding ──────────────────────────────────────────────

LAYER1_SYSTEM = """You are an expert QA engineer and web analyst.
Your job is to analyse raw DOM data from a web page and produce a structured semantic understanding of it.
Always respond with valid JSON only. No explanation, no markdown, just JSON."""

LAYER1_PROMPT = """Analyse the following DOM data extracted from a web page and return a JSON object.

DOM DATA:
{dom_data}

Return a JSON object with this exact structure:
{{
  "url": "<page url>",
  "page_type": "<one of: landing, login, registration, product_listing, product_detail, cart, checkout, dashboard, form, search, profile, settings, other>",
  "page_purpose": "<one sentence describing what this page does>",
  "primary_actions": ["<list of main things a user can do on this page>"],
  "user_journeys": ["<list of typical user journeys that pass through this page>"],
  "critical_elements": ["<ids or descriptions of the most important interactive elements>"],
  "risk_areas": ["<areas that are likely to have bugs or need careful testing>"],
  "testability_score": <integer 1-10>,
  "notes": "<any important observations for a tester>"
}}"""


# ─── Layer 2: Field Analysis ───────────────────────────────────────────────────

LAYER2_SYSTEM = """You are an expert QA automation engineer specialising in form testing and input validation.
You analyse web form fields and generate comprehensive test data strategies.
Always respond with valid JSON only."""

LAYER2_PROMPT = """You are analysing form fields for a web page. Based on the page understanding and raw field data below, produce a detailed field analysis.

PAGE UNDERSTANDING:
{page_understanding}

RAW FIELDS:
{fields_data}

Return a JSON object with this structure:
{{
  "url": "<page url>",
  "forms": [
    {{
      "form_id": "<form id or index>",
      "form_purpose": "<what this form does>",
      "fields": [
        {{
          "name": "<field name/id>",
          "type": "<field type>",
          "label": "<human readable label>",
          "required": <true/false>,
          "validation_rules": ["<list of inferred validation rules>"],
          "test_data": {{
            "valid": ["<2-3 valid test values>"],
            "invalid": ["<2-3 invalid values that should trigger errors>"],
            "boundary": ["<boundary/edge case values>"],
            "empty": "<what happens when left empty>"
          }},
          "risk_level": "<low|medium|high>"
        }}
      ],
      "submission_scenarios": [
        {{
          "scenario_name": "<scenario>",
          "description": "<what this tests>",
          "field_values": {{"<field_name>": "<value>"}},
          "expected_outcome": "<what should happen>"
        }}
      ]
    }}
  ]
}}"""


# ─── Layer 3: Test Strategy ────────────────────────────────────────────────────

LAYER3_SYSTEM = """You are a senior QA automation engineer who writes Gauge test specifications.
You generate test scenarios as Gauge spec steps — plain English strings that a human can read.
You MUST follow the exact Gauge step format shown. Always respond with valid JSON only."""

LAYER3_PROMPT = """Generate Gauge test scenarios for the following web page.

PAGE UNDERSTANDING:
{page_understanding}

FIELD ANALYSIS:
{field_analysis}

RELEVANT CONTEXT:
{rag_context}

CRITICAL RULES FOR GAUGE STEPS:
1. Steps must be plain English — NO CSS selectors, NO XPath, NO HTML in steps
2. Steps must come from this ALLOWED STEPS LIST only:
   - Navigate to "<url>"
   - Enter search term "<value>"
   - Click the search button
   - Enter email "<value>"
   - Enter password "<value>"
   - Click the login button
   - Enter loan amount "<value>"
   - Enter interest rate "<value>"
   - Enter loan term "<value>"
   - Enter house price "<value>"
   - Enter down payment "<value>"
   - Select down payment unit "<value>"
   - Enter sale price "<value>"
   - Enter incentive "<value>"
   - Enter trade in value "<value>"
   - Enter sale tax "<value>"
   - Enter title and registration "<value>"
   - Enter starting principal "<value>"
   - Enter annual addition "<value>"
   - Select compound frequency "<value>"
   - Enter years "<value>"
   - Enter current age "<value>"
   - Enter retirement age "<value>"
   - Enter life expectancy "<value>"
   - Enter current income "<value>"
   - Enter income growth rate "<value>"
   - Enter desired retirement income "<value>"
   - Select income unit "<value>"
   - Enter expected return "<value>"
   - Enter inflation rate "<value>"
   - Enter other income "<value>"
   - Enter current savings "<value>"
   - Enter annual contribution "<value>"
   - Select contribution unit "<value>"
   - Click the calculate button
   - Verify the page contains "<text>"
   - Verify monthly payment is displayed
   - Verify amortization schedule is displayed
   - Verify the user is logged in
3. DO NOT invent new step names. Only use steps from the list above.
4. Every scenario must start with: Navigate to "<url>"
5. XSS payloads like <script>alert('xss')</script> must be written as the safe string "xss-attack-string" instead
6. Tags must use underscores not hyphens: happy_path not happy-path

Return a JSON object with this exact structure:
{{
  "url": "<page url>",
  "page_type": "<page type>",
  "priority": "<high|medium|low>",
  "module_name": "<SHORT ALL-CAPS MODULE NAME e.g. MORTGAGE, LOGIN, HOME>",
  "test_scenarios": [
    {{
      "scenario_id": "<e.g. TC_001>",
      "title": "<clear scenario title>",
      "category": "<happy_path|negative|boundary|e2e>",
      "tags": ["<tag1>", "<tag2>"],
      "steps": [
        "<exact Gauge step string from allowed list above>",
        "<exact Gauge step string from allowed list above>"
      ],
      "expected_result": "<what should happen>"
    }}
  ]
}}

Generate exactly 4 scenarios per page: happy_path, negative, boundary, e2e.
Steps must be strings — not objects."""


# ─── RAG Context Template ─────────────────────────────────────────────────────

RAG_CONTEXT_TEMPLATE = """The following are relevant past test cases and knowledge for this type of page:

{retrieved_chunks}

Use this to inform your test strategy but don't duplicate scenarios."""
