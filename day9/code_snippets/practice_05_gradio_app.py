"""
Practice 05: Simple Gradio PDF Q&A App
======================================
Goal: Turn the RAG pipeline into a small browser app.

Run:
    python practice_05_gradio_app.py
Then open the local URL shown in the terminal.

Needs:
    GROQ_API_KEY set in your terminal environment or .env file.
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import gradio as gr
from groq import Groq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

MODEL = "llama-3.1-8b-instant"
CHROMA_DIR = Path("chroma_gradio_app")
COLLECTION_NAME = "gradio_rag"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K = 4

SYSTEM_PROMPT = """You are a document-based AI assistant.
Answer ONLY using the retrieved context.
If the answer is not in the context, say:
I could not find that in the uploaded document.
Include page numbers for factual claims."""

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def get_pdf_path(pdf_file) -> str | None:
    """Handle different Gradio versions: file may be a string path or file object."""
    if pdf_file is None:
        return None
    if isinstance(pdf_file, str):
        return pdf_file
    if hasattr(pdf_file, "name"):
        return pdf_file.name
    return None


def display_page(doc) -> int | str:
    page = doc.metadata.get("page")
    return page + 1 if isinstance(page, int) else "?"


def build_vector_store(pdf_file):
    pdf_path = get_pdf_path(pdf_file)
    if not pdf_path:
        return None, "Please upload a PDF first."

    try:
        pages = PyPDFLoader(pdf_path).load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents(pages)

        if CHROMA_DIR.exists():
            shutil.rmtree(CHROMA_DIR)

        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=str(CHROMA_DIR),
            collection_name=COLLECTION_NAME,
        )
        return vector_store, f"Indexed {len(pages)} pages into {len(chunks)} chunks. Ready!"
    except Exception as e:
        return None, f"Indexing failed: {e}"


def format_context(docs) -> str:
    parts = []
    for i, doc in enumerate(docs, start=1):
        parts.append(f"[Source {i} | page {display_page(doc)}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def answer_question(message, history, vector_store):
    if vector_store is None:
        return "Please upload and index a PDF first."

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "GROQ_API_KEY is missing. Set it before running the app."

    retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K})
    docs = retriever.invoke(message)
    context = format_context(docs)

    prompt = f"""Question: {message}

Retrieved context:
{context}

Answer using only the retrieved context. Include page references."""

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


with gr.Blocks(title="PDF Q&A RAG Assistant") as demo:
    gr.Markdown("# PDF Q&A RAG Assistant")
    gr.Markdown("Upload a PDF, click **Index PDF**, then ask questions.")

    vector_state = gr.State(value=None)

    with gr.Row():
        pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
        index_button = gr.Button("Index PDF", variant="primary")

    status = gr.Textbox(label="Status", interactive=False)
    index_button.click(
        fn=build_vector_store,
        inputs=pdf_input,
        outputs=[vector_state, status],
    )

    chat = gr.ChatInterface(
        fn=answer_question,
        additional_inputs=[vector_state],
        title="Ask your document",
        examples=[
            ["What are the main topics covered?"],
            ["What does the document say about deadlines?"],
            ["Summarise the key points from page 1."],
        ],
    )


if __name__ == "__main__":
    demo.launch()
