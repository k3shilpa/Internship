# rag/retriever.py - RAG Retriever: indexes knowledge base and retrieves context

import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from rag.embedder import Embedder
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """
    Indexes the knowledge base and past test results into the vector store,
    then retrieves relevant context for the AI strategy layer.
    """

    def __init__(self):
        self.embedder = Embedder()
        self.store    = VectorStore()

    def build_index(self):
        """Index the site knowledge base and any past execution results."""
        logger.info("RAG: Building index...")
        self.store.clear()
        count = 0

        # Index knowledge base
        if os.path.exists(config.KNOWLEDGE_BASE_PATH):
            try:
                with open(config.KNOWLEDGE_BASE_PATH) as f:
                    kb = json.load(f)
                for entry in kb.get("test_patterns", []):
                    text = f"{entry.get('title', '')} {entry.get('description', '')} {' '.join(entry.get('steps', []))}"
                    vector = self.embedder.embed(text)
                    self.store.add(
                        doc_id=f"kb_{count}",
                        text=text,
                        vector=vector,
                        metadata={"source": "knowledge_base", "type": entry.get("type", "")},
                    )
                    count += 1
                logger.info(f"RAG: Indexed {count} knowledge base entries.")
            except Exception as e:
                logger.warning(f"RAG: Failed to index knowledge base: {e}")

        # Index past execution results
        if os.path.exists(config.EXECUTION_RESULTS_PATH):
            try:
                with open(config.EXECUTION_RESULTS_PATH) as f:
                    results = json.load(f)
                for r in results:
                    scenario = r.get("scenario", "")
                    status   = r.get("status", "")
                    text     = f"Past test: {scenario} — Result: {status}"
                    if r.get("failure_reason"):
                        text += f" — Failure: {r['failure_reason']}"
                    vector = self.embedder.embed(text)
                    self.store.add(
                        doc_id=f"result_{count}",
                        text=text,
                        vector=vector,
                        metadata={"source": "execution_results"},
                    )
                    count += 1
            except Exception as e:
                logger.warning(f"RAG: Failed to index execution results: {e}")

        self.store.save()
        logger.info(f"RAG: Index built with {len(self.store)} total entries.")

    def retrieve(self, query: str, top_k: int = None) -> list[str]:
        """Return the most relevant text chunks for a query."""
        if len(self.store) == 0:
            logger.debug("RAG: Store is empty, skipping retrieval.")
            return []

        query_vector = self.embedder.embed(query)
        results = self.store.search(query_vector, top_k=top_k or config.RAG_TOP_K)
        chunks = [r["text"] for r in results if r["score"] > 0.3]
        logger.debug(f"RAG: Retrieved {len(chunks)} chunks for query: '{query[:60]}'")
        return chunks
