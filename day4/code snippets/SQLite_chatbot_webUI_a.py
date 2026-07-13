import os
import sqlite3
from groq import Groq
import gradio as gr

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# Connect to SQLite database
# check_same_thread=False allows Gradio to use the database safely
conn = sqlite3.connect("memory_sqlite.db", check_same_thread=False)
cursor = conn.cursor()

# Create table to store conversation history
# We only store:
# - role: user or assistant
# - content: actual message
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY,
    role TEXT,
    content TEXT
)
""")
conn.commit()


def save_memory(role, content):
    # Save each conversation message into database
    cursor.execute(
        "INSERT INTO history (role, content) VALUES (?, ?)",
        (role, content)
    )
    conn.commit()


def search_memory(prompt):
    matched = {}

    for keyword in prompt.split():
        keyword = keyword.strip("?.!,").lower()

        # Skip very short words like is, my, a, to
        if len(keyword) <= 3:
            continue

        cursor.execute(
            "SELECT id, role, content FROM history WHERE LOWER(content) LIKE ?",
            (f"%{keyword}%",)
        )

        for row_id, role, content in cursor.fetchall():
            matched[row_id] = f"{role}: {content}"

    return "\n".join(matched.values())


def chat_bot(prompt, history):
    
    # Step 1: Search past memory using current prompt
    relevant_memory = search_memory(prompt)

    # Step 2: Send retrieved memory + current prompt to LLM
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
    title="SQLite Memory Bot"
).launch()