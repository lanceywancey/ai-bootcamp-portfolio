import os
import json
from groq import Groq
import gradio as gr

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# File for storing conversation history
JSON_FILE = "chat.json"

# File for storing static user profile info
# Example: skills, preferences, background info
MD_FILE = "test_skills.md"


# Load previous conversation history from JSON file
def load_chat_memory():
    try:
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    except:
        # Return empty list if file doesn't exist yet
        return []


# Save updated conversation history back to JSON file
def save_chat_memory(memory):
    with open(JSON_FILE, "w") as f:
        json.dump(memory, f)


# Load fixed profile knowledge from markdown file
# This acts like long-term memory
def load_profile():
    try:
        with open(MD_FILE, "r") as f:
            return f.read()
    except:
        return ""


def chat_bot(prompt, history):
    
    # Load previous chat memory
    chat_memory = load_chat_memory()

    # Load fixed profile memory
    profile_memory = load_profile()

    # Add current user message into chat history
    chat_memory.append({
        "role": "user",
        "content": prompt
    })

    # Start messages with profile memory
    messages = [
        {
            "role": "system",
            "content": f"User profile:\n{profile_memory}"
        }
    ]

    # Add previous conversation history
    messages.extend(chat_memory)

    # Send everything to LLM
    response = client.chat.completions.create(
        messages=messages,
        model="llama-3.1-8b-instant"
    )

    reply = response.choices[0].message.content

    # Save assistant reply into chat history
    chat_memory.append({
        "role": "assistant",
        "content": reply
    })

    # Store updated conversation
    save_chat_memory(chat_memory)

    return reply


# Launch chatbot UI
gr.ChatInterface(
    fn=chat_bot,
    title="Hybrid Memory Chatbot"
).launch()