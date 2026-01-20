import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

# =====================================================
# 1. Configuration (NO hardcoding)
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", os.path.join(BASE_DIR, "faiss_index"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
TOP_K = int(os.getenv("TOP_K", 3))

# =====================================================
# 2. Load vector database
# =====================================================
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

vectorstore = FAISS.load_local(
    VECTOR_DB_DIR,
    embeddings,
    allow_dangerous_deserialization=True
)

retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

# =====================================================
# 3. STRICT Prompt (NO hallucination)
# =====================================================
PROMPT_TEMPLATE = """
You are an assistant answering questions strictly based on the provided stand-up meeting context.

Rules (VERY IMPORTANT):
- Answer ONLY if the information is explicitly stated in the context.
- Do NOT infer, count, guess, or combine information.
- Do NOT mention chunks, sources, or internal details.
- If the answer is not explicitly mentioned, reply EXACTLY:
  "Not mentioned in the meeting."

Context:
{context}

Question:
{question}

Answer:
"""

prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)

# =====================================================
# 4. LLaMA 3 (Generation)
# =====================================================
llm = Ollama(model=LLM_MODEL)

# =====================================================
# 5. RAG QA Function (FIXED)
# =====================================================
def ask(question: str) -> str:
    # Use invoke() instead of deprecated method
    docs = retriever.invoke(question)

    if not docs:
        return "Not mentioned in the meeting."

    # IMPORTANT: Do NOT expose chunk IDs
    context = "\n\n".join(d.page_content for d in docs)

    final_prompt = prompt.format(
        context=context,
        question=question
    )

    response = llm.invoke(final_prompt)

    # Safety net (force exact fallback)
    if not response or response.strip().lower() in {
        "not mentioned",
        "not mentioned.",
        "n/a"
    }:
        return "Not mentioned in the meeting."

    return response.strip()

# =====================================================
# 6. Interactive Mode
# =====================================================
if __name__ == "__main__":
    print("\nRAG Q&A using LLaMA 3 (Ollama)")
    print("Type 'exit' to quit")

    while True:
        q = input("\nAsk a question: ").strip()
        if q.lower() == "exit":
            break
        print("\nAnswer:", ask(q))
