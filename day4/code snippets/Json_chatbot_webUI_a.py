import os
import json
from groq import Groq
import gradio as gr

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# JSON file used to store chat history
FILE = "chat.json"


def load_memory():
    try:
        # Load previous conversation history
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        # Return empty list if no history exists yet
        return []


def save_memory(memory):
    # Save updated conversation history
    with open(FILE, "w") as f:
        json.dump(memory, f)


def chat_bot(prompt, history):
    # Load previous memory
    memory = load_memory()

    # Add current user message
    memory.append({
        "role": "user",
        "content": prompt
    })

    # Send full conversation history to LLM
    response = client.chat.completions.create(
        messages=memory,
        model="llama-3.1-8b-instant"
    )

    reply = response.choices[0].message.content

    # Save assistant reply
    memory.append({
        "role": "assistant",
        "content": reply
    })

    # Store updated history for future chats
    save_memory(memory)

    return reply


# Launch chatbot UI
gr.ChatInterface(
    fn=chat_bot,
    title="JSON Memory Bot"
).launch()