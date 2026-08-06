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

"""
Final local document Q&A chatbot.

Run:
    streamlit run practice_06_final_streamlit_local_doc_chatbot.py

Before offline use:
    pip install streamlit requests pypdf python-docx
    ollama pull qwen2.5:1.5b
    ollama pull nomic-embed-text

After dependencies and models are available, this app can run without internet.
"""

import json
import math
import os
from pathlib import Path
import tempfile

import requests
import streamlit as st

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:1.5b")
EMBED_MODEL = os.getenv("LOCAL_EMBED_MODEL", "nomic-embed-text")


def read_uploaded_file(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix in {".txt", ".md", ".py", ".csv", ".html"}:
        return uploaded_file.getvalue().decode("utf-8", errors="ignore")

    if suffix == ".pdf":
        from pypdf import PdfReader
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        reader = PdfReader(tmp_path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    if suffix == ".docx":
        import docx
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        document = docx.Document(tmp_path)
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())

    raise ValueError(f"Unsupported file type: {suffix}")


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    clean = " ".join(text.split())
    chunks = []
    start = 0
    while start < len(clean):
        chunks.append(clean[start:start + chunk_size])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def embed_text(text: str) -> list[float]:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def build_index(uploaded_files, chunk_size: int, overlap: int) -> list[dict]:
    records = []
    for uploaded_file in uploaded_files:
        text = read_uploaded_file(uploaded_file)
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        for idx, chunk in enumerate(chunks):
            records.append({
                "filename": uploaded_file.name,
                "chunk_index": idx,
                "text": chunk,
                "embedding": embed_text(chunk),
            })
    return records


def retrieve(query: str, records: list[dict], top_k: int) -> list[dict]:
    q_vec = embed_text(query)
    scored = []
    for record in records:
        score = cosine_similarity(q_vec, record["embedding"])
        item = dict(record)
        item["score"] = score
        scored.append(item)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def ask_local_llm(question: str, sources: list[dict], strict_mode: bool) -> str:
    context = "\n\n".join(
        f"[Source {i}: {s['filename']} / chunk {s['chunk_index']}]\n{s['text']}"
        for i, s in enumerate(sources, start=1)
    )

    if strict_mode:
        instruction = (
            "Answer using ONLY the retrieved sources. "
            "If the answer is not present, say you could not find it in the documents. "
            "Cite sources like [Source 1]."
        )
    else:
        instruction = (
            "Use the retrieved sources when relevant. "
            "If the sources do not contain enough information, clearly say what comes from the documents "
            "and what is general knowledge."
        )

    messages = [
        {"role": "system", "content": "You are a helpful local document Q&A assistant. " + instruction},
        {"role": "user", "content": f"Question:\n{question}\n\nSources:\n{context}\n\nAnswer:"},
    ]

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={"model": CHAT_MODEL, "messages": messages, "stream": False, "options": {"temperature": 0.2}},
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


st.set_page_config(page_title="Local Document Q&A", layout="wide")
st.title("🖥️ Local Document Q&A Chatbot")
st.caption("Runs with Ollama on your own machine after models and dependencies are installed.")

with st.sidebar:
    st.header("Settings")
    st.write(f"Chat model: `{CHAT_MODEL}`")
    st.write(f"Embedding model: `{EMBED_MODEL}`")
    chunk_size = st.slider("Chunk size", min_value=400, max_value=1600, value=900, step=100)
    overlap = st.slider("Overlap", min_value=0, max_value=400, value=150, step=50)
    top_k = st.slider("Retrieved chunks", min_value=2, max_value=8, value=4)
    strict_mode = st.checkbox("Strict mode: answer only from documents", value=True)

uploaded_files = st.file_uploader(
    "Upload one or more documents",
    type=["txt", "md", "py", "csv", "html", "pdf", "docx"],
    accept_multiple_files=True,
)

if "records" not in st.session_state:
    st.session_state.records = []

if uploaded_files and st.button("Build local index"):
    with st.spinner("Reading, chunking, and embedding documents locally..."):
        st.session_state.records = build_index(uploaded_files, chunk_size, overlap)
    st.success(f"Indexed {len(st.session_state.records)} chunks from {len(uploaded_files)} file(s).")

question = st.text_input("Ask a question about the uploaded documents:")

if question and st.session_state.records:
    with st.spinner("Retrieving relevant chunks and asking the local model..."):
        sources = retrieve(question, st.session_state.records, top_k)
        answer = ask_local_llm(question, sources, strict_mode)

    st.subheader("Answer")
    st.write(answer)

    st.subheader("Retrieved Sources")
    for i, source in enumerate(sources, start=1):
        with st.expander(f"Source {i}: {source['filename']} | chunk {source['chunk_index']} | score={source['score']:.3f}"):
            st.write(source["text"])
elif question and not st.session_state.records:
    st.warning("Please upload documents and click 'Build local index' first.")
