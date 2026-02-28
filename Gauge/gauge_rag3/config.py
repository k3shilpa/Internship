"""
config.py - Central configuration for AI Gauge Testing Framework
"""

import os
from pathlib import Path

# ─── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
METADATA_DIR = DATA_DIR / "metadata"
TESTCASES_DIR = DATA_DIR / "testcases"
SPECS_DIR = DATA_DIR / "specs"
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
REPORTS_DIR = BASE_DIR / "reports" / "output"
CHROMA_DIR = BASE_DIR / ".chromadb"

# Create all directories if they don't exist
for d in [METADATA_DIR, TESTCASES_DIR, SPECS_DIR, REPORTS_DIR, CHROMA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Groq API ──────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Fast, within free tier
GROQ_MAX_TOKENS = 4096
GROQ_TEMPERATURE = 0.3  # Low temp = more deterministic test cases

# Rate limit handling
GROQ_REQUESTS_PER_MINUTE = 30      # Conservative limit for free tier
GROQ_TOKENS_PER_MINUTE = 14_400   # Free tier limit
GROQ_RETRY_ATTEMPTS = 3
GROQ_RETRY_DELAY = 10              # Seconds between retries
GROQ_BATCH_SIZE = 5                # Elements per AI batch call

# ─── Crawler Settings ──────────────────────────────────────────────────────────
CRAWLER_MAX_PAGES = int(os.getenv("MAX_PAGES", "10"))
CRAWLER_MAX_DEPTH = 2
CRAWLER_TIMEOUT = 30               # Seconds per page
CRAWLER_HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
CRAWLER_WAIT_TIME = 2              # Seconds to wait for JS to load

# Element types to extract
CRAWLER_EXTRACT_ELEMENTS = [
    "button", "a", "input", "select", "textarea",
    "form", "table", "nav", "header", "footer",
    "h1", "h2", "h3", "img", "label"
]

# ─── RAG Settings ──────────────────────────────────────────────────────────────
RAG_EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, local, no API cost
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 5                      # Number of relevant chunks to retrieve
RAG_COLLECTION_NAME = "testing_knowledge_base"

# Knowledge base paths
KNOWLEDGE_SOURCES = {
    "test_cases": KNOWLEDGE_BASE_DIR / "test_cases",
    "best_practices": KNOWLEDGE_BASE_DIR / "best_practices",
    "selenium_gauge_docs": KNOWLEDGE_BASE_DIR / "selenium_gauge_docs",
}

# ─── Gauge Settings ────────────────────────────────────────────────────────────
GAUGE_PROJECT_DIR = BASE_DIR / "gauge_project"
GAUGE_SPECS_DIR = GAUGE_PROJECT_DIR / "specs"
GAUGE_STEP_IMPL_FILE = GAUGE_PROJECT_DIR / "step_impl.py"
GAUGE_REPORTS_DIR = GAUGE_PROJECT_DIR / "reports"

# ─── Test Case Schema ──────────────────────────────────────────────────────────
# This defines what the AI must output
TEST_CASE_SCHEMA = {
    "test_suite": "string",         # Name of the test suite
    "url": "string",                # Tested URL
    "generated_at": "datetime",
    "test_cases": [
        {
            "id": "string",             # TC_001
            "name": "string",           # Human-readable test name
            "category": "string",       # functional | navigation | form | ui | e2e
            "priority": "string",       # high | medium | low
            "description": "string",    # What is being tested
            "preconditions": ["string"],
            "steps": [
                {
                    "step_number": "int",
                    "action": "string",     # click | type | verify | navigate | select
                    "target": {
                        "element_type": "string",
                        "selector_type": "string",  # css | xpath | id | name
                        "selector_value": "string",
                        "description": "string"
                    },
                    "input_data": "string | null",
                    "expected_result": "string"
                }
            ],
            "expected_outcome": "string",
            "tags": ["string"]
        }
    ]
}
