# rag/vector_store.py - Simple JSON-backed vector store

import json
import logging
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Lightweight local vector store backed by a JSON file.
    Uses cosine similarity for retrieval — no external DB required.
    """

    def __init__(self, path: str = None):
        self.path    = path or config.VECTOR_STORE_PATH
        self.entries: list[dict] = []  # {id, text, metadata, vector}
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    self.entries = json.load(f)
                logger.info(f"VectorStore: loaded {len(self.entries)} entries from {self.path}")
            except Exception as e:
                logger.warning(f"VectorStore: could not load {self.path}: {e}")
                self.entries = []

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.entries, f)
        logger.info(f"VectorStore: saved {len(self.entries)} entries to {self.path}")

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def add(self, doc_id: str, text: str, vector: list[float], metadata: dict = None):
        # Replace if exists
        self.entries = [e for e in self.entries if e["id"] != doc_id]
        self.entries.append({
            "id": doc_id,
            "text": text,
            "vector": vector,
            "metadata": metadata or {},
        })

    def clear(self):
        self.entries = []

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def search(self, query_vector: list[float], top_k: int = None) -> list[dict]:
        """Return top-k entries by cosine similarity."""
        top_k = top_k or config.RAG_TOP_K
        if not self.entries or not query_vector:
            return []

        scored = []
        for entry in self.entries:
            score = _cosine_similarity(query_vector, entry["vector"])
            scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"score": s, **e} for s, e in scored[:top_k]]

    def __len__(self):
        return len(self.entries)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
