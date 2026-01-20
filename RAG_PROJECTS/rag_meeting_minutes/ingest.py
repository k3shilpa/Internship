import os
import sys
import shutil
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

# =====================================================
# 1. Load configuration
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", os.path.join(BASE_DIR, "faiss_index"))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 300))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))

# =====================================================
# 2. Validate input file
# =====================================================
if len(sys.argv) < 2:
    raise ValueError(
        " Usage: python ingest.py <text_file>\n"
        "Example: python ingest.py standup_meeting.txt"
    )

file_name = sys.argv[1]
DATA_PATH = os.path.join(DATA_DIR, file_name)

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f" File not found: {DATA_PATH}")

# =====================================================
# 3. Load stand-up / speech text
# =====================================================
loader = TextLoader(DATA_PATH, encoding="utf-8")
documents = loader.load()
print(f"Loaded file: {file_name}")

# =====================================================
# 4. Chunking
# =====================================================
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", " "]
)

chunks = splitter.split_documents(documents)

for i, chunk in enumerate(chunks):
    chunk.metadata.update({
        "chunk_id": i,
        "source_file": file_name,
        "content_type": "standup_speech"
    })

print(f"Created {len(chunks)} chunks")

# =====================================================
# 5. Ollama embeddings
# =====================================================
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

# =====================================================
# 6. Clean previous vector DB
# =====================================================
if os.path.exists(VECTOR_DB_DIR):
    shutil.rmtree(VECTOR_DB_DIR)
    print(" Old vector store removed")

# =====================================================
# 7. Create FAISS index
# =====================================================
vectorstore = FAISS.from_documents(chunks, embeddings)

# =====================================================
# 8. Save vector DB
# =====================================================
vectorstore.save_local(VECTOR_DB_DIR)
print(" Stand-up meeting text indexed successfully")
