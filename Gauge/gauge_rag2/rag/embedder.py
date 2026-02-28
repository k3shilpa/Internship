# rag/embedder.py - Text embedding using Ollama

import logging
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_layers.ai_utils import get_embedding

logger = logging.getLogger(__name__)


class Embedder:
    """Wraps Ollama embedding calls with caching."""

    def __init__(self):
        self._cache: dict[str, list[float]] = {}

    def embed(self, text: str) -> list[float]:
        """Return embedding vector for the given text. Results are cached."""
        if text in self._cache:
            return self._cache[text]
        vector = get_embedding(text)
        self._cache[text] = vector
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts."""
        results = []
        for i, text in enumerate(texts):
            logger.debug(f"Embedding {i+1}/{len(texts)}")
            results.append(self.embed(text))
        return results
