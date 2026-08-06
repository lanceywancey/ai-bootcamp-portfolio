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

import os
import requests

from practice_04_retrieve_test import retrieve

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:1.5b")


def build_grounded_prompt(question: str, chunks: list[dict]) -> list[dict]:
    """
    Build a prompt that asks the model to answer only from retrieved chunks.
    The source labels let us show where the answer came from.
    """
    context_lines = []
    for i, chunk in enumerate(chunks, start=1):
        context_lines.append(
            f"[Source {i}: {chunk['filename']} / chunk {chunk['chunk_index']}]\n{chunk['text']}"
        )

    context = "\n\n".join(context_lines)

    system = (
        "You are a careful local document assistant. "
        "Answer using ONLY the provided sources. "
        "If the answer is not in the sources, say: 'I could not find this in the provided documents.' "
        "Cite sources using [Source 1], [Source 2], etc."
    )

    user = f"""Question:
{question}

Retrieved document sources:
{context}

Answer:"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def ask_ollama(messages: list[dict]) -> str:
    payload = {
        "model": CHAT_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=180)
    response.raise_for_status()
    return response.json()["message"]["content"]


def answer_question(question: str, top_k: int = 4) -> tuple[str, list[dict]]:
    chunks = retrieve(question, top_k=top_k)
    messages = build_grounded_prompt(question, chunks)
    answer = ask_ollama(messages)
    return answer, chunks


if __name__ == "__main__":
    print("Local Document Q&A CLI")
    print("Type 'exit' to stop.\n")

    while True:
        question = input("Question: ").strip()
        if question.lower() in {"exit", "quit"}:
            break

        answer, sources = answer_question(question)
        print("\nAnswer:\n", answer)
        print("\nSources:")
        for i, source in enumerate(sources, start=1):
            print(f"[Source {i}] {source['filename']} | chunk {source['chunk_index']} | score={source['score']:.3f}")
        print("-" * 80)
