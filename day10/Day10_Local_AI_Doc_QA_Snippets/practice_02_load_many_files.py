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

from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".csv", ".html", ".pdf", ".docx"}


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_pdf_file(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("Install pypdf first: pip install pypdf")

    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"\n\n--- Page {i} ---\n{text}")
    return "\n".join(pages)


def read_docx_file(path: Path) -> str:
    try:
        import docx
    except ImportError:
        raise ImportError("Install python-docx first: pip install python-docx")

    document = docx.Document(str(path))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def load_one_file(path: Path) -> dict:
    """Load one supported file and return metadata + text."""
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md", ".py", ".csv", ".html"}:
        text = read_text_file(path)
    elif suffix == ".pdf":
        text = read_pdf_file(path)
    elif suffix == ".docx":
        text = read_docx_file(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    return {
        "filename": path.name,
        "path": str(path),
        "extension": suffix,
        "text": text,
        "characters": len(text),
    }


def load_folder(folder: str = "docs") -> list[dict]:
    """Load all supported files from a folder."""
    folder_path = Path(folder)
    if not folder_path.exists():
        folder_path.mkdir()
        print(f"Created folder: {folder_path.resolve()}")
        print("Put your documents inside this folder, then run again.")
        return []

    documents = []
    for path in sorted(folder_path.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                doc = load_one_file(path)
                documents.append(doc)
                print(f"✅ Loaded {doc['filename']} ({doc['characters']:,} characters)")
            except Exception as e:
                print(f"⚠️ Skipped {path.name}: {e}")

    print(f"\nTotal loaded files: {len(documents)}")
    return documents


if __name__ == "__main__":
    docs = load_folder("docs")
    for doc in docs[:2]:
        print("\nPreview:", doc["filename"])
        print(doc["text"][:500])
