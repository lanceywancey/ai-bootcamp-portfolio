"""
Practice 04: Inspect Retrieval Quality
======================================
Goal: Debug RAG before blaming the LLM.
This simple practice compares top-k settings and shows what chunks were retrieved.

Run AFTER practice_02:
    python practice_04_inspect_retrieval.py
"""

from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = Path("chroma_rag_demo")
COLLECTION_NAME = "rag_demo"


def display_page(doc) -> int | str:
    page = doc.metadata.get("page")
    return page + 1 if isinstance(page, int) else "?"


def show_results(vector_store, question: str, k: int) -> None:
    print(f"\n{'=' * 70}")
    print(f"Question: {question}")
    print(f"top-k = {k}")

    docs = vector_store.similarity_search(question, k=k)
    for i, doc in enumerate(docs, start=1):
        preview = doc.page_content[:350].replace("\n", " ")
        print(f"\nResult {i} | page {display_page(doc)}")
        print(preview)


def main() -> None:
    if not CHROMA_DIR.exists():
        raise FileNotFoundError("Chroma index not found. Run practice_02_embed_store.py first.")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )

    question = "What happens if I submit my assignment late?"
    for k in [1, 2, 4, 8]:
        show_results(vector_store, question, k)

    print("\nTeaching point:")
    print("- top-k too low: may miss evidence")
    print("- top-k too high: may include noisy unrelated context")
    print("- Always inspect retrieved chunks before changing the prompt or model")


if __name__ == "__main__":
    main()
