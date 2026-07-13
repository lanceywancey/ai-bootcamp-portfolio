import os
import sqlite3
import json
import numpy as np
from groq import Groq
import gradio as gr
from sentence_transformers import SentenceTransformer

# Connect to Groq API (make sure GROQ_API_KEY is set in your environment)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Load embedding model to convert text into vectors
# These vectors help us compare meaning (semantic similarity)
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


# Connect to SQLite database
# check_same_thread=False allows Gradio to access database safely
conn = sqlite3.connect("memory_sql_S.db", check_same_thread=False)
cursor = conn.cursor()

# Create memory table if it doesn't already exist
# We store:
# - role: who said it (user/assistant)
# - content: actual message
# - embedding: vector version of message
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY,
    role TEXT,
    content TEXT,
    embedding TEXT
)
""")
conn.commit()


def save_memory(role, content):
    # Convert text into embedding vector
    embedding = embed_model.encode(content).tolist()

    # Save role, message content, and embedding into database
    cursor.execute(
        "INSERT INTO history (role, content, embedding) VALUES (?, ?, ?)",
        (role, content, json.dumps(embedding))
    )
    conn.commit()


def semantic_search_memory(prompt):
    # Convert current user prompt into embedding
    query_embedding = embed_model.encode(prompt)

    # Load all previous memories from database
    cursor.execute("SELECT content, embedding FROM history")
    rows = cursor.fetchall()

    results = []

    for content, embedding_text in rows:
        # Convert stored embedding back into numpy array
        memory_embedding = np.array(json.loads(embedding_text))

        # Calculate cosine similarity
        # Higher score = more relevant memory
        score = np.dot(query_embedding, memory_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(memory_embedding)
        )

        results.append((score, content))

    # Sort memories from most relevant to least relevant
    results.sort(reverse=True)

    # Keep only top 3 most relevant memories
    top_results = results[:3]

    return "\n".join([content for score, content in top_results])


def chat_bot(prompt, history):
    
    # Step 1: Retrieve relevant past memories
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
    title="SQLite Semantic Memory Bot"
).launch()