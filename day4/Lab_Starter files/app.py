"""
PROJECT 1 — Context-Aware Chatbot with Memory

Your task is to build a chatbot that can remember useful information from
previous messages and use that memory to answer later questions.

This chatbot should be able to:

1. Build a working chatbot interface
   - You may use Gradio or a simple CLI.
   - The chatbot should accept user input and return an AI response.

2. Maintain conversation history
   - Store both user messages and assistant replies.
   - Use recent conversation history so the chatbot can understand context.

3. Store memory
   - Use JSON, SQLite, or ChromaDB.
   - For the basic version, SQLite or JSON is enough.
   - Each message should be saved with at least:
       role      -> "user" or "assistant"
       content   -> the message text
       timestamp -> when the message was saved

4. Retrieve relevant memory
   - Do not send the entire history to the model every time.
   - Retrieve only useful memory.
   - Basic version: keyword search.
   - Advanced version: semantic search using embeddings / ChromaDB.

5. Use provided files from Moodle
   - Load skills.md as learner profile or background knowledge.
   - Load memory_seed.json as structured starting memory.
   - Add both into the system prompt when helpful.

6. Apply prompt engineering
   - Write a clear system prompt.
   - Tell the model how to use memory.
   - Tell the model not to invent personal facts.
   - Tell the model to say “I don’t know” if memory does not contain the answer.

7. Bonus features
   - Add summarization when the conversation becomes long.
   - Support multiple users with separate memory.
   - Improve latency by limiting how much memory is sent to the model.

Suggested structure:

- setup database / memory file
- load skills.md
- load memory_seed.json
- save_memory()
- search_memory()
- get_recent_history()
- build_messages()
- chat_bot()
- Gradio or CLI interface

Important idea:
main chatbot function should not do everything by itself.
It should coordinate smaller helper functions, similar to the AI pipeline idea:
input -> retrieve memory -> build prompt -> call model -> save response -> return output.
"""

import os
import json
from pathlib import Path
from groq import Groq
import gradio as gr
from datetime import datetime
from dotenv import load_dotenv

ENV_FILE = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=ENV_FILE, override=True)

# Connect to Groq API
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# File for storing conversation history
CHAT_FILE = "chat.json"

MEMORY_SEED_FILE = "memory_seed.json"

# File for storing static user profile info
# Example: skills, preferences, background info
MD_FILE = "skills.md"

def load_memory():
    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        # Return empty list if file doesn't exist yet
        return []

def load_memory_seed():
    try:
        with open(MEMORY_SEED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_memory(memory):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)
        f.write("\n")

def search_memory(memory, query):
    # Basic keyword search for relevant memory
    relevant = []
    for entry in memory:
        if query.lower() in entry["content"].lower():
            relevant.append(entry)
    return relevant

def get_recent_history(memory, n=5):
    # Get the last n messages from memory
    return memory[-n:]

def get_timestamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def build_messages(prompt, memory, profile, seed_memory):
    # Start with system prompt including profile info
    system_prompt = f"""
    You are a helpful chatbot.

    Use the user's profile and memory when relevant.
    Do not invent personal facts.
    If the answer is not in the memory, say "I don't know."

    User profile:
    {profile}

    Starting memory:
    {json.dumps(seed_memory, indent=2)}
    """



    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]
    
    # Add relevant memory entries
    relevant_memory = search_memory(memory, prompt)
    for entry in relevant_memory:
        messages.append({
            "role": entry["role"],
            "content": entry["content"]
        })
    
    # Add recent conversation history
    recent_history = get_recent_history(memory)
    for entry in recent_history:
        messages.append({
            "role": entry["role"],
            "content": entry["content"]
        })
    
    # Finally, add the current user prompt
    messages.append({
        "role": "user",
        "content": prompt,
    })
    
    return messages

def chat_bot(prompt, history):
    # Load previous chat memory
    chat_memory = load_memory()
    seed_memory = load_memory_seed()

    # Load fixed profile memory
    try:
        with open(MD_FILE, "r") as f:
            profile_memory = f.read()
    except:
        profile_memory = ""

    # Build messages for the model
    messages = build_messages(prompt, chat_memory, profile_memory, seed_memory)

    # Send messages to the model
    response = client.chat.completions.create(
        messages=messages,
        model="llama-3.1-8b-instant"
    )

    reply = response.choices[0].message.content

    # Save current conversation for future use
    chat_memory.append({
        "role": "user",
        "content": prompt,
        "timestamp": get_timestamp()
    })
    chat_memory.append({
        "role": "assistant",
        "content": reply,
        "timestamp": get_timestamp()
    })
    save_memory(chat_memory)

    return reply

# Launch chatbot UI
gr.ChatInterface(
    fn=chat_bot,
    title="Context-Aware Chatbot with Memory"
).launch()

