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
import math
import os
from pathlib import Path
import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("LOCAL_EMBED_MODEL", "nomic-embed-text")


def embed_text(text: str) -> list[float]:
    payload = {"model": EMBED_MODEL, "input": text}
    response = requests.post(f"{OLLAMA_BASE_URL}/api/embed", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["embeddings"][0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Simple cosine similarity without external libraries."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve(query: str, store_path: str = "local_vector_store.json", top_k: int = 4) -> list[dict]:
    records = json.loads(Path(store_path).read_text(encoding="utf-8"))
    query_vector = embed_text(query)

    scored = []
    for record in records:
        score = cosine_similarity(query_vector, record["embedding"])
        scored.append((score, record))

    scored.sort(key=lambda item: item[0], reverse=True)

    results = []
    for score, record in scored[:top_k]:
        record = dict(record)
        record["score"] = score
        results.append(record)

    return results


if __name__ == "__main__":
    question = input("Ask a question about your documents: ")
    results = retrieve(question, top_k=4)

    print("\nTop retrieved chunks:")
    for i, item in enumerate(results, start=1):
        print(f"\n[{i}] {item['filename']} | chunk {item['chunk_index']} | score={item['score']:.3f}")
        print(item["text"][:500], "...")
