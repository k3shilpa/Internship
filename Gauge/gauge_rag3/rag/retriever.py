"""
rag/retriever.py
================
Retrieves relevant chunks from ChromaDB.
Imported by test_generator.py.
Can also be run standalone to test retrieval.

HOW TO RUN (optional debug, from project root):
    python rag/retriever.py

ALL SETTINGS ARE HARDCODED BELOW.
No config file, no CLI arguments, no relative imports.
"""

import logging
import os

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
#  SETTINGS — must match embedder.py
# =============================================================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_DIR      = ".chromadb"
COLLECTION_NAME = "testing_knowledge_base"
TOP_K           = 5      # how many chunks to retrieve per query

# Used only when running this file directly to test retrieval:
TEST_QUERY = "form validation test cases for login page"

# =============================================================================

_model = None
_col   = None


def _init():
    global _model, _col
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    if _col is None:
        client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        try:
            _col = client.get_collection(COLLECTION_NAME)
            logger.info(f"Vector store ready: {_col.count()} chunks")
        except:
            logger.warning("Collection not found — run: python rag/embedder.py")
            _col = None


def retrieve(query):
    """Return formatted context string for the given query."""
    _init()
    if _col is None or _col.count() == 0:
        return ""
    try:
        emb  = _model.encode(query).tolist()
        res  = _col.query(
            query_embeddings=[emb],
            n_results=min(TOP_K, _col.count()),
            include=["documents", "metadatas", "distances"]
        )
        results = [
            {"text": d, "source": m.get("source", "?"), "score": round(1 - dist, 3)}
            for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
        ]
        return _format(results)
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return ""


def retrieve_for_page(page_data):
    """Build a query from crawled page metadata and retrieve context."""
    ptype = page_data.get("page_type", "general")
    elems = page_data.get("elements", {})
    parts = []
    if elems.get("forms"):       parts.append(f"{len(elems['forms'])} form(s)")
    if elems.get("interactive"): parts.append(f"{len(elems['interactive'])} button(s)")
    if elems.get("navigation"):  parts.append(f"{len(elems['navigation'])} link(s)")
    if elems.get("tables"):      parts.append(f"{len(elems['tables'])} table(s)")
    query = f"Test cases for {ptype} page with {', '.join(parts) or 'general elements'}"
    logger.info(f"  RAG query: {query}")
    return retrieve(query)


def _format(results):
    by_src = {}
    for r in results:
        by_src.setdefault(r["source"], []).append(r)
    labels = {
        "test_cases":          "EXAMPLE TEST CASES",
        "best_practices":      "TESTING BEST PRACTICES",
        "selenium_gauge_docs": "FRAMEWORK DOCS",
    }
    lines = []
    for src, chunks in by_src.items():
        lines.append(f"--- {labels.get(src, src.upper())} ---")
        for c in chunks:
            lines.append(c["text"])
            lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(f"\n{'='*55}")
    print(f"RAG RETRIEVER TEST")
    print(f"Query: {TEST_QUERY}")
    print(f"{'='*55}\n")
    _init()
    ctx = retrieve(TEST_QUERY)
    print(ctx if ctx else "(no results — run python rag/embedder.py first)")