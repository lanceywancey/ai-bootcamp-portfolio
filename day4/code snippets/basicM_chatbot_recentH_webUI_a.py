import os
from groq import Groq
import gradio as gr

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Store conversation history while program is running
memory = []


def chat_bot(prompt, history):
    global memory

    # Save current user message
    memory.append({
        "role": "user",
        "content": prompt
    })

    # Keep only the most recent 6 messages
    # Older messages are ignored
    recent_memory = memory[-6:]

    # Send only recent memory to LLM
    chat_completion = client.chat.completions.create(
        messages=recent_memory,
        model="llama-3.1-8b-instant"
    )

    reply = chat_completion.choices[0].message.content

    # Save assistant reply
    memory.append({
        "role": "assistant",
        "content": reply
    })

    return reply


# Launch chatbot UI
gr.ChatInterface(
    fn=chat_bot,
    title="Rolling Memory Chatbot",
    description="This bot only remembers recent conversations."
).launch()