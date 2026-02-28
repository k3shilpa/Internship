# config.py - Central Configuration for AI-Driven Gauge Tester

import os

# ─── Groq API Settings ────────────────────────────────────────────────────────
# Get your free API key at: https://console.groq.com/
# Set in PowerShell: $env:GROQ_API_KEY = "gsk_your-key-here"
GROK_API_KEY    = os.getenv("GROQ_API_KEY", "")
GROK_BASE_URL   = "https://api.groq.com/openai/v1"
GROK_MODEL      = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROK_TIMEOUT    = int(os.getenv("GROQ_TIMEOUT", "120"))

# ─── RAG / Embedding Settings ─────────────────────────────────────────────────
# Embeddings use sentence-transformers locally — no API key needed.
# Model: all-MiniLM-L6-v2 (~80MB, downloaded once to ~/.cache/huggingface)
VECTOR_STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vector_store.json")
RAG_TOP_K         = int(os.getenv("RAG_TOP_K", "3"))

# ─── Selenium / Chrome Settings ───────────────────────────────────────────────
CHROME_HEADLESS       = os.getenv("CHROME_HEADLESS", "false").lower() == "true"
CHROME_WINDOW_SIZE    = "1920,1080"
IMPLICIT_WAIT         = 10    # seconds
PAGE_LOAD_TIMEOUT     = 30    # seconds
SCREENSHOT_ON_FAILURE = True

# ─── Target Application ───────────────────────────────────────────────────────
TARGET_URL      = os.getenv("TARGET_URL", "https://www.calculator.net/")
MAX_CRAWL_DEPTH = int(os.getenv("MAX_CRAWL_DEPTH", "2"))
MAX_PAGES       = int(os.getenv("MAX_PAGES", "10"))

# ─── Test Generation Settings ─────────────────────────────────────────────────
MAX_SCENARIOS_PER_PAGE  = int(os.getenv("MAX_SCENARIOS_PER_PAGE", "4"))
INCLUDE_NEGATIVE_TESTS  = os.getenv("INCLUDE_NEGATIVE_TESTS", "true").lower() == "true"
INCLUDE_BOUNDARY_TESTS  = os.getenv("INCLUDE_BOUNDARY_TESTS", "true").lower() == "true"

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR               = os.path.dirname(os.path.abspath(__file__))
DATA_DIR               = os.path.join(BASE_DIR, "data")
REPORTS_DIR            = os.path.join(BASE_DIR, "reports")
SPECS_DIR              = os.path.join(BASE_DIR, "specs")
KNOWLEDGE_BASE_PATH    = os.path.join(BASE_DIR, "knowledge_base", "site_knowledge.json")

DOM_DATA_PATH          = os.path.join(DATA_DIR, "dom_data.json")
PAGE_ANALYSIS_PATH     = os.path.join(DATA_DIR, "page_analysis.json")
FIELD_ANALYSIS_PATH    = os.path.join(DATA_DIR, "field_analysis.json")
TEST_STRATEGY_PATH     = os.path.join(DATA_DIR, "test_strategy.json")
EXECUTION_RESULTS_PATH = os.path.join(DATA_DIR, "execution_results.json")
GENERATED_SPEC_PATH    = os.path.join(SPECS_DIR, "generated_test.spec")

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE  = os.path.join(BASE_DIR, "logs", "pipeline.log")
