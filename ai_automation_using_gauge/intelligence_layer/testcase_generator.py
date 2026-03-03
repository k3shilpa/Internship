"""
Test Case Generator
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
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an expert QA engineer specialising in exploratory web testing.
Given a DOM analysis of a web page and relevant testing patterns,
generate comprehensive exploratory test cases.

Return ONLY a valid JSON array. Each element must have:
{
  "title": "Short descriptive title",
  "category": "functional|navigation|form|accessibility|edge_case|security",
  "steps": ["Step 1 description", "Step 2 description", ...],
  "expected": "Expected result after all steps"
}

Be thorough. Cover happy paths, edge cases, error states, accessibility, and security basics.
Return 8-15 test cases. No markdown, no prose - pure JSON array only."""


class TestCaseGenerator:
    def __init__(self):
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def generate(self, dom_data: dict[str, Any], rag_context: str) -> list[dict]:
        response = _get_client().chat.completions.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": self._build_prompt(dom_data, rag_context)},
            ],
        )
        raw = response.choices[0].message.content.strip()
        return self._parse_response(raw)

    def _build_prompt(self, dom_data: dict, rag_context: str) -> str:
        return f"""## DOM Analysis
{dom_data.get('summary', '')}

## Forms Detail
{json.dumps(dom_data.get('forms', []), indent=2)[:2000]}

## Buttons
{json.dumps(dom_data.get('buttons', []), indent=2)[:1000]}

## Relevant Testing Patterns (RAG Context)
{rag_context[:3000]}

## Task
Generate exploratory test cases for this web application."""

    def _parse_response(self, raw: str) -> list[dict]:
        clean = re.sub(r"```(?:json)?", "", raw).strip()
        start, end = clean.find("["), clean.rfind("]")
        if start == -1 or end == -1:
            return []
        try:
            cases = json.loads(clean[start : end + 1])
            result = []
            for tc in cases:
                if isinstance(tc, dict) and "title" in tc and "steps" in tc:
                    result.append({
                        "title":    str(tc.get("title", "Untitled")),
                        "category": str(tc.get("category", "exploratory")),
                        "steps":    [str(s) for s in tc.get("steps", [])],
                        "expected": str(tc.get("expected", "")),
                        "status":   None,
                    })
            return result
        except json.JSONDecodeError:
            return []
```

---

### `rag_data/testing_patterns.txt`
```
# Web Application Testing Patterns

## 1. Form Validation Testing
Always test forms with:
- Empty submissions (all required fields blank)
- Boundary values (min/max length, numeric ranges)
- Special characters: <, >, &, ", ', ;, --
- XSS probe: <script>alert(1)</script> in text fields
- Whitespace-only input
- Very long strings (over 1000 characters)
- Unicode and emoji characters
- Copy-paste behaviour vs typed input

## 2. Authentication Testing
- Login with valid credentials
- Login with wrong password
- Login with unregistered email
- Login with SQL injection strings
- Session timeout behaviour
- Remember-me functionality
- Password reset flow
- Account lockout after N failed attempts
- Concurrent login from multiple browsers

## 3. Navigation and Routing
- All navigation links return 200, not 404
- Back-button behaviour after form submission
- Deep-linking directly to internal routes
- Bookmarking and sharing URLs
- Breadcrumb accuracy
- Mobile hamburger menu functionality

## 4. State Management
- Data persists after page refresh
- Multi-tab consistency
- Cart/basket state across sessions
- Draft-save functionality
- Undo/redo where available

## 5. Error Handling
- Network offline simulation
- Server error pages (check for stack trace leakage)
- 404 page has navigation back to home
- Timeout handling for slow API calls
- File upload with wrong file type
- File size limits enforced

## 6. Accessibility (WCAG 2.1 AA)
- Full keyboard navigation without mouse
- Tab order is logical
- All images have alt text
- Form labels associated with inputs
- Colour contrast ratio at least 4.5:1
- Focus indicator visible at all times
- ARIA roles on dynamic components
- Screen-reader announcements on route change

## 7. Performance Basics
- Page load time under 3 seconds
- Images lazy-loaded below the fold
- Interactions respond within 100ms

## 8. Responsive / Cross-browser
- 320px viewport renders correctly
- 768px tablet renders correctly
- 1440px desktop renders correctly
- Test in Chrome, Firefox, Safari, Edge

## 9. Search Functionality
- Empty query returns all or shows prompt
- Single character returns results
- No-results state displays helpful message
- Special characters in search do not break results
- Search results are sorted relevantly
- Pagination works for large result sets

## 10. Data Table / List Views
- Sorting by each column
- Filtering reduces list correctly
- Select-all and bulk actions
- Pagination edge cases (last page, single-page)
- Empty state when no results
```

---

### `rag_data/web_elements_guide.txt`
```
# Web Elements Testing Guide

## Input Fields

### Text Input
- maxlength attribute enforced visually and on submit
- Autocomplete behaviour
- Copy-paste of formatted text
- Drag-and-drop text into field

### Password Fields
- Characters masked by default
- Show/hide toggle works
- Browser autofill integration

### Email Inputs
- Valid: user@domain.com
- Invalid: missing @, missing TLD, double dots
- Plus-addressing: user+tag@domain.com

### Number Inputs
- Spinner arrows increment/decrement
- Manual typing outside min/max
- Decimal precision enforced
- Negative numbers where not expected

### Date/Time Pickers
- Date in past when future required
- Date beyond max allowed
- Timezone awareness
- Manual keyboard entry vs calendar picker

### File Upload
- Accepted MIME types enforced
- Max file size limit
- Multiple file selection
- Drag-and-drop zone
- Progress indicator for large files
- Cancel mid-upload

### Checkboxes and Radios
- Default selection state
- Tab focus and space-bar activation
- Group validation (at least one required)

### Dropdowns / Select
- Default placeholder option
- Long option lists (scrollable, searchable)
- Keyboard navigation through options
- Dynamic option loading

## Buttons

### Submit Buttons
- Disabled after first click to prevent double submit
- Visual loading state while processing
- Re-enabled after error response
- Keyboard activation with Enter or Space

### Toggle Buttons
- State reflected in aria-pressed
- Colour change visible

### Danger/Destructive Buttons
- Confirmation dialog before action
- Confirmation can be cancelled

## Modals and Dialogs
- Focus moves to modal on open
- Focus trapped inside modal while open
- Closed with Escape key
- Background scroll locked while open
- Screen reader announces modal role

## Tables
- Column headers have scope attribute
- Sortable columns announce sort direction
- Row selection highlights row
- Responsive horizontal scroll at small widths

## Navigation
- Current page highlighted in nav
- Skip-to-content link at top of page
- Dropdown menus keyboard-operable
- Mega-menus close on Escape

## Notifications / Toasts
- Auto-dismiss timing
- Manual dismiss available
- Multiple stacked notifications
- Error notifications persist until dismissed
- ARIA live region for screen readers

## Infinite Scroll / Load More
- Loads additional items on scroll or click
- Loading spinner shows during fetch
- End-of-list message when no more items
- Focus management after new items loaded