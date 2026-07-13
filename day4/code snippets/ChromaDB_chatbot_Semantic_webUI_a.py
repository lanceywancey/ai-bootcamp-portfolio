import os
import chromadb
from groq import Groq
import gradio as gr
from sentence_transformers import SentenceTransformer

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Load embedding model
# Converts text into vectors for semantic search
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


# Create persistent Chroma database
# Data will remain saved even after restarting program
chroma_client = chromadb.PersistentClient(path="chroma_memory")

# Create (or load existing) memory collection
collection = chroma_client.get_or_create_collection("history")


def save_memory(role, content):
    # Convert message into embedding vector
    embedding = embed_model.encode(content).tolist()

    # Store message, embedding, and metadata in ChromaDB
    collection.add(
        documents=[content],
        embeddings=[embedding],
        metadatas=[{"role": role}],
        ids=[str(collection.count())]   # simple unique ID
    )


def semantic_search_memory(prompt):
    # If no previous memory exists
    if collection.count() == 0:
        return "No memory yet."

    # Convert current prompt into embedding
    query_embedding = embed_model.encode(prompt).tolist()

    # Chroma automatically handles similarity search
    # No need to manually calculate cosine similarity
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    # Return top 3 most relevant memories
    return "\n".join(results["documents"][0])


def chat_bot(prompt, history):
    
    # Step 1: Retrieve relevant memory
    relevant_memory = semantic_search_memory(prompt)

    # Step 2: Send memory + current prompt to LLM
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"Relevant memory:\n{relevant_memory}"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.1-8b-instant"
    )

    reply = response.choices[0].message.content

    # Step 3: Save current conversation into memory
    save_memory("user", prompt)
    save_memory("assistant", reply)

    return reply


# Launch chatbot UI
gr.ChatInterface(
    fn=chat_bot,
    title="ChromaDB Semantic Memory Bot"
).launch()