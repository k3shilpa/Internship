"""
rag/embedder.py
===============
Indexes knowledge_base/ docs into ChromaDB for RAG retrieval.
Run once before generating test cases.

HOW TO RUN (from the project root folder):
    python rag/embedder.py

ALL SETTINGS ARE HARDCODED BELOW — edit and run.
No config file, no CLI arguments, no relative imports.
"""

import json
import logging
import hashlib
import os

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
#  SETTINGS — edit these values directly
# =============================================================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"            # local model, no API needed
CHROMA_DIR      = ".chromadb"                    # ChromaDB storage folder
COLLECTION_NAME = "testing_knowledge_base"

CHUNK_SIZE      = 500    # words per chunk
CHUNK_OVERLAP   = 50     # overlap words between chunks

REBUILD         = False  # True = wipe existing index and start fresh

# Knowledge base folders to index (relative paths from project root)
KNOWLEDGE_SOURCES = {
    "test_cases":          "knowledge_base/test_cases",
    "best_practices":      "knowledge_base/best_practices",
    "selenium_gauge_docs": "knowledge_base/selenium_gauge_docs",
}

# =============================================================================

os.makedirs(CHROMA_DIR, exist_ok=True)


def run():
    logger.info(f"\n{'='*55}")
    logger.info(f"EMBEDDER  |  model={EMBEDDING_MODEL}  rebuild={REBUILD}")
    logger.info(f"{'='*55}")

    logger.info("Loading embedding model...")
    model  = SentenceTransformer(EMBEDDING_MODEL)
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )

    if REBUILD:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info("Old index deleted.")
        except:
            pass

    try:
        col = client.get_collection(COLLECTION_NAME)
        logger.info(f"Existing collection loaded: {col.count()} chunks")
    except:
        col = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        logger.info("New collection created.")

    total = 0
    for source_name, folder_path in KNOWLEDGE_SOURCES.items():
        if not os.path.isdir(folder_path):
            logger.warning(f"Folder not found: {folder_path}  (skipping)")
            continue
        logger.info(f"\nIndexing: {source_name}  ({folder_path})")
        chunks = _process_folder(folder_path, source_name)
        _store(model, col, chunks)
        total += len(chunks)
        logger.info(f"  {len(chunks)} chunks stored")

    logger.info(f"\nDone — {total} new chunks  |  total in DB: {col.count()}")
    logger.info(f"\nNext step: python ai_engine/test_generator.py")


def _process_folder(folder, source_name):
    chunks = []
    for root, _, files in os.walk(folder):
        for fname in files:
            if not any(fname.endswith(ext) for ext in [".txt", ".md", ".json"]):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    raw = f.read()
                if fname.endswith(".json"):
                    try:
                        raw = json.dumps(json.loads(raw), indent=2)
                    except:
                        pass
                words = raw.split()
                if len(words) <= CHUNK_SIZE:
                    parts = [raw]
                else:
                    step  = CHUNK_SIZE - CHUNK_OVERLAP
                    parts = [" ".join(words[i:i + CHUNK_SIZE]) for i in range(0, len(words), step) if words[i:i + CHUNK_SIZE]]
                for i, chunk in enumerate(parts):
                    cid = hashlib.md5(f"{fpath}_{i}".encode()).hexdigest()
                    chunks.append({"id": cid, "text": chunk,
                                   "meta": {"source": source_name, "file": fname, "chunk": i}})
                logger.info(f"  {fname}  ({len(parts)} chunks)")
            except Exception as e:
                logger.warning(f"  Could not read {fname}: {e}")
    return chunks


def _store(model, col, chunks, batch=50):
    for i in range(0, len(chunks), batch):
        b    = chunks[i:i + batch]
        embs = model.encode([c["text"] for c in b], show_progress_bar=False).tolist()
        col.upsert(
            ids=[c["id"] for c in b],
            embeddings=embs,
            documents=[c["text"] for c in b],
            metadatas=[c["meta"] for c in b],
        )


if __name__ == "__main__":
    run()
