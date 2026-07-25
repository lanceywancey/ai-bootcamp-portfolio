"""
Practice 03: Retrieve + Generate (Full RAG Pipeline)
======================================================
Goal: Load the ChromaDB index built in practice_02, retrieve the top-k
      relevant chunks for a question, then ask Groq to answer using ONLY
      those chunks. This is the complete RAG pipeline in one file.

RAG Pipeline Stage: Step 5 (Retrieve) + Step 6 (Generate)

Run AFTER practice_02 (which builds the ChromaDB index on disk).
Run: python practice_03_retrieve_generate.py
"""

import os
from dotenv import load_dotenv
from groq import Groq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

CHROMA_DIR   = "./chroma_rag_demo"      # Same dir as practice_02
TOP_K        = 4                        # Number of chunks to retrieve

SYSTEM_PROMPT = """You are a document-based AI assistant.
Answer ONLY using the context provided below.
If the answer is not in the context, say exactly:
  "I could not find that information in the provided documents."
Always include the page number when referencing a fact."""

# ── SETUP ──────────────────────────────────────────────────────────────────────
print("🔧 Setting up embedding model and vector store...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Load the existing ChromaDB index (no re-embedding needed)
vector_store = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name="rag_demo",
)

retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K})
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def format_context(docs):
    """Turn retrieved Document objects into a readable context string."""
    parts = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "?")
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Source {i} | {source} | page {page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)

def ask(question: str):
    print(f"\n{'='*60}")
    print(f"❓ Question: {question}")

    # Step 5: Retrieve
    docs = retriever.invoke(question)
    print(f"\n📋 Retrieved {len(docs)} chunks:")
    for doc in docs:
        print(f"   • page {doc.metadata.get('page','?')} — {doc.page_content[:80]}...")

    # Step 6: Generate
    context = format_context(docs)
    prompt = f"""Question: {question}

Retrieved context:
{context}

Answer using ONLY the context above. Include page references."""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content
    print(f"\n🤖 Answer:\n{answer}")
    return answer

# ── INTERACTIVE LOOP ───────────────────────────────────────────────────────────
print("\n✅ RAG pipeline ready. Type your questions (or 'quit' to exit).\n")
while True:
    question = input("Your question: ").strip()
    if question.lower() in ("quit", "exit", "q"):
        break
    if question:
        ask(question)
