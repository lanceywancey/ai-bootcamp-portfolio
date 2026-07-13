import os
from groq import Groq
import gradio as gr

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Short-term memory: stores recent messages
memory = []

# Long-term compressed memory: stores summary of older messages
summary = ""


def summarize_memory():
    global memory, summary

    # Convert recent messages into plain text for summarization
    text = "\n".join([f"{m['role']}: {m['content']}" for m in memory])

    # Ask the LLM to summarize the recent conversation
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Summarize this conversation briefly:\n{text}"
            }
        ],
        model="llama-3.1-8b-instant"
    )

    # Save summary and clear detailed memory
    summary = response.choices[0].message.content
    memory = []


def chat_bot(prompt, history):
    global memory, summary

    # Save current user message
    memory.append({
        "role": "user",
        "content": prompt
    })

    messages = []

    # Add previous summary if it exists
    if summary:
        messages.append({
            "role": "system",
            "content": f"Conversation summary so far: {summary}"
        })

    # Add recent conversation messages
    messages.extend(memory)

    # Send summary + recent messages to LLM
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.1-8b-instant"
    )

    reply = chat_completion.choices[0].message.content

    # Save assistant reply
    memory.append({
        "role": "assistant",
        "content": reply
    })

    # If memory becomes too long, summarize and reset it
    if len(memory) > 8:
        summarize_memory()

    return reply


# Launch chatbot UI
gr.ChatInterface(
    fn=chat_bot,
    title="Summary Memory Chatbot",
    description="This bot keeps recent messages and summarizes older conversation."
).launch()