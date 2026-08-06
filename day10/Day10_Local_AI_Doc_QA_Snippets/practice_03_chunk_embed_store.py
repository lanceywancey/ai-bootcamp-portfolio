"""
Day 10 Local AI - Document Q&A Project
Run fully offline AFTER:
1) Python dependencies are installed
2) Ollama is installed
3) Required models are pulled once

Suggested models:
    ollama pull qwen2.5:1.5b
    ollama pull nomic-embed-text

You can change model names with:
    Windows CMD:
        set LOCAL_LLM_MODEL=qwen2.5:1.5b
        set LOCAL_EMBED_MODEL=nomic-embed-text
    PowerShell:
        $env:LOCAL_LLM_MODEL="qwen2.5:1.5b"
        $env:LOCAL_EMBED_MODEL="nomic-embed-text"
    macOS/Linux:
        export LOCAL_LLM_MODEL=qwen2.5:1.5b
        export LOCAL_EMBED_MODEL=nomic-embed-text
"""

import json
import os
from pathlib import Path
import requests

from practice_02_load_many_files import load_folder

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("LOCAL_EMBED_MODEL", "nomic-embed-text")


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """
    Split text into overlapping chunks.
    Overlap helps preserve meaning when an answer spans two nearby chunks.
    """
    clean = " ".join(text.split())
    chunks = []
    start = 0

    while start < len(clean):
        end = start + chunk_size
        chunk = clean[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks


def embed_text(text: str) -> list[float]:
    """Ask Ollama to create one embedding vector locally."""
    payload = {"model": EMBED_MODEL, "input": text}
    response = requests.post(f"{OLLAMA_BASE_URL}/api/embed", json=payload, timeout=120)
    response.raise_for_status()
    embeddings = response.json().get("embeddings", [])
    if not embeddings:
        raise RuntimeError("No embedding returned. Check your embedding model.")
    return embeddings[0]


def build_vector_store(docs_folder: str = "docs", output_path: str = "local_vector_store.json") -> None:
    """Load many files, chunk them, embed each chunk, and save everything as JSON."""
    documents = load_folder(docs_folder)
    records = []

    for doc in documents:
        chunks = chunk_text(doc["text"])
        print(f"\n📄 {doc['filename']} -> {len(chunks)} chunks")

        for index, chunk in enumerate(chunks):
            print(f"  embedding chunk {index + 1}/{len(chunks)}", end="\r")
            vector = embed_text(chunk)
            records.append({
                "id": f"{doc['filename']}::chunk_{index:04d}",
                "filename": doc["filename"],
                "path": doc["path"],
                "chunk_index": index,
                "text": chunk,
                "embedding": vector,
            })
        print()

    Path(output_path).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Saved {len(records)} chunks to {output_path}")


if __name__ == "__main__":
    build_vector_store("docs", "local_vector_store.json")
