"""
Practice 01: Load & Chunk a PDF
=================================
Goal: Understand how PyPDFLoader converts a PDF into Document objects,
      and how RecursiveCharacterTextSplitter breaks those into chunks.

RAG Pipeline Stage: Step 1 (Load) + Step 2 (Chunk)

Run: python practice_01_load_chunk.py
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── STEP 1: Load PDF ──────────────────────────────────────────────────────────
# Replace "sample.pdf" with any PDF you have locally
PDF_PATH = "sample.pdf"

print("📄 Loading PDF...")
loader = PyPDFLoader(PDF_PATH)
pages = loader.load()   # Returns a list of Document objects (one per page)

print(f"   Pages loaded: {len(pages)}")
print(f"   Metadata of page 1: {pages[0].metadata}")
print(f"\n   First 400 characters of page 1:\n")
print(pages[0].page_content[:400])
print("   ...")

# ── STEP 2: Split into chunks ─────────────────────────────────────────────────
# Each chunk will become one "retrievable unit" in the vector store.
# chunk_size   = max characters per chunk  (try 300–1000)
# chunk_overlap = characters shared between adjacent chunks (20% of chunk_size)
# separators   = priority order for split points → paragraphs → sentences → words

print("\n✂️  Splitting into chunks...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " ", ""],
)
chunks = splitter.split_documents(pages)

print(f"   Total chunks: {len(chunks)}")
print(f"\n   Sample chunk (chunk #2):")
print(f"   Metadata: {chunks[1].metadata}")
print(f"   Content : {chunks[1].page_content[:300]}\n")

# ── EXPERIMENT ─────────────────────────────────────────────────────────────────
# Try changing chunk_size to 200 or 1500 and see how the count changes.
# Smaller chunks = more precise but less context per chunk.
# Larger chunks = more context but might include irrelevant text.
print("💡 Tip: Change chunk_size and chunk_overlap above, re-run, and compare.")
