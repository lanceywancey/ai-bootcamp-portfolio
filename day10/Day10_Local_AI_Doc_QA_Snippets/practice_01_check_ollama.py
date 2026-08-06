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

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:1.5b")
EMBED_MODEL = os.getenv("LOCAL_EMBED_MODEL", "nomic-embed-text")


def check_ollama_server() -> bool:
    """Check whether Ollama is running on localhost."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        print("✅ Ollama server is running.")
        print(f"Found {len(models)} installed model(s):")
        for model in models:
            print(" -", model.get("name"))
        return True
    except requests.RequestException as e:
        print("❌ Could not connect to Ollama.")
        print("Start Ollama first, then try again.")
        print("Command to test manually:")
        print("    ollama list")
        print("    ollama serve")
        print("Error:", e)
        return False


def test_chat_model(prompt: str = "Explain local AI in one simple sentence.") -> None:
    """Send one small prompt to the local chat model."""
    payload = {
        "model": CHAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=120)
    response.raise_for_status()
    print("\n✅ Chat model response:")
    print(response.json()["message"]["content"])


def test_embedding_model(text: str = "Local AI keeps data on my computer.") -> None:
    """Create an embedding vector using a local embedding model."""
    payload = {"model": EMBED_MODEL, "input": text}
    response = requests.post(f"{OLLAMA_BASE_URL}/api/embed", json=payload, timeout=120)
    response.raise_for_status()
    embeddings = response.json().get("embeddings", [])
    if embeddings:
        print("\n✅ Embedding model response:")
        print(f"Vector length: {len(embeddings[0])}")
        print(f"First 5 values: {embeddings[0][:5]}")
    else:
        print("⚠️ No embedding returned. Check your embedding model name.")


if __name__ == "__main__":
    if check_ollama_server():
        test_chat_model()
        test_embedding_model()
