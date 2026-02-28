"""
rag/vector_store.py
===================
ChromaDB wrapper — imported by retriever.py, not run directly.
"""

import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

# =============================================================================
#  ✏️  EDIT THESE SETTINGS  (must match embedder.py)
# =============================================================================

CHROMA_DIR      = Path(__file__).parent.parent / ".chromadb"
COLLECTION_NAME = "testing_knowledge_base"

# =============================================================================


class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def __init__(self):
        if self._ready:
            return
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        try:
            self.col = self.client.get_collection(COLLECTION_NAME)
            logger.info(f"✅ Vector store: {self.col.count()} chunks")
        except Exception:
            logger.warning("⚠️  Collection not found — run: python rag/embedder.py")
            self.col = None
        self._ready = True

    def is_ready(self) -> bool:
        return self.col is not None and self.col.count() > 0

    def query(self, embedding: list, n: int = 5) -> list:
        if not self.is_ready():
            return []
        try:
            r = self.col.query(
                query_embeddings=[embedding],
                n_results=min(n, self.col.count()),
                include=["documents", "metadatas", "distances"]
            )
            return [
                {"text": d, "source": m.get("source","?"),
                 "file": m.get("file","?"), "score": round(1 - dist, 3)}
                for d, m, dist in zip(
                    r["documents"][0], r["metadatas"][0], r["distances"][0]
                )
            ]
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []
