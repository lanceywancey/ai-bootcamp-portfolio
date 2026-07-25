"""
Practice 02: Embed Text & Store in ChromaDB
============================================
Goal: Convert text chunks into vectors using a local embedding model,
      then persist them in ChromaDB for semantic search.

RAG Pipeline Stage: Step 3 (Embed) + Step 4 (Store)

Dependencies:
    pip install langchain-huggingface langchain-chroma chromadb sentence-transformers

Run: python practice_02_embed_store.py
Note: First run downloads the MiniLM model (~80 MB). Subsequent runs are fast.
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

PDF_PATH = "sample.pdf"
CHROMA_DIR = "./chroma_rag_demo"

# ── STEP 1 + 2: Load & Chunk (reused from practice_01) ───────────────────────
print("📄 Loading and chunking PDF...")
loader = PyPDFLoader(PDF_PATH)
pages = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
chunks = splitter.split_documents(pages)
print(f"   {len(chunks)} chunks ready for embedding")

# ── STEP 3: Create the embedding model ───────────────────────────────────────
# all-MiniLM-L6-v2: free, local, 384-dimensional vectors
# Runs on CPU — no GPU or API key required!
print("\n🔢 Loading embedding model (all-MiniLM-L6-v2)...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Sanity check: embed a single query and show its shape
test_vector = embeddings.embed_query("What is the deadline?")
print(f"   Vector dimensions: {len(test_vector)}")   # Should print 384
print(f"   First 5 values  : {[round(v, 4) for v in test_vector[:5]]}")

# ── STEP 4: Store in ChromaDB ─────────────────────────────────────────────────
# Chroma stores: the text, its embedding vector, and any metadata (page, source)
# persist_directory makes it permanent on disk — you won't need to re-embed next time.
print(f"\n🗄️  Storing {len(chunks)} chunks in ChromaDB at '{CHROMA_DIR}'...")
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=CHROMA_DIR,
    collection_name="rag_demo",
)
print(f"   ✅ Done! Collection has {vector_store._collection.count()} vectors.")

# ── QUICK SIMILARITY CHECK ─────────────────────────────────────────────────────
query = "What is the attendance policy?"
print(f"\n🔍 Quick test — searching for: '{query}'")
results = vector_store.similarity_search(query, k=2)
for i, doc in enumerate(results, 1):
    print(f"\n   Result {i} (page {doc.metadata.get('page', '?')}):")
    print(f"   {doc.page_content[:200]}...")

print("\n💡 Tip: The vectors are now saved on disk. Run practice_03 to retrieve them.")
