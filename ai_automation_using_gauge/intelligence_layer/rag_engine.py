"""
RAG Engine
Loads static knowledge from rag_data/, embeds with sentence-transformers,
indexes with FAISS, and retrieves relevant chunks for a given query.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

import numpy as np

RAG_DATA_DIR = Path(__file__).parent.parent / "rag_data"
CHUNK_SIZE   = int(os.getenv("RAG_CHUNK_SIZE", 500))
TOP_K        = int(os.getenv("RAG_TOP_K", 5))


class RAGEngine:
    def __init__(self):
        self._model  = None
        self._index  = None
        self._chunks: List[str] = []
        self._build_index()

    def query(self, query: str, top_k: int = TOP_K) -> str:
        if not self._chunks:
            return ""
        q_emb = self._encode([query])
        distances, indices = self._index.search(q_emb, min(top_k, len(self._chunks)))
        retrieved = [self._chunks[i] for i in indices[0] if i < len(self._chunks)]
        return "\n\n---\n\n".join(retrieved)

    def _load_docs(self) -> List[str]:
        chunks = []
        for txt_file in RAG_DATA_DIR.glob("*.txt"):
            content = txt_file.read_text(encoding="utf-8", errors="ignore")
            for i in range(0, len(content), CHUNK_SIZE - 50):
                chunk = content[i : i + CHUNK_SIZE].strip()
                if len(chunk) > 100:
                    chunks.append(chunk)
        return chunks

    def _encode(self, texts: List[str]) -> np.ndarray:
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return (embeddings / np.maximum(norms, 1e-10)).astype("float32")

    def _build_index(self):
        import faiss
        from sentence_transformers import SentenceTransformer

        self._model  = SentenceTransformer("all-MiniLM-L6-v2")
        self._chunks = self._load_docs()

        if not self._chunks:
            return

        embeddings   = self._encode(self._chunks)
        dim          = embeddings.shape[1]
        self._index  = faiss.IndexFlatIP(dim)
        self._index.add(embeddings)