import os
from groq import Groq
import gradio as gr
from dotenv import load_dotenv
load_dotenv()

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Basic memory storage
# Stores all conversation messages while program is running
memory = []


def chat_bot(prompt, history):
    # Save current user message into memory
    memory.append({
        "role": "user",
        "content": prompt
    })

    # Send full memory list to LLM
    chat_completion = client.chat.completions.create(
        messages=memory,
        model="llama-3.1-8b-instant"
    )

    reply = chat_completion.choices[0].message.content

    # Save assistant reply into memory
    memory.append({
        "role": "assistant",
        "content": reply
    })

    return reply


# Launch chatbot UI
gr.ChatInterface(
    fn=chat_bot,
    title="Basic Memory Chatbot",
    description="Now we simply store all previous conversations in a list."
).launch()