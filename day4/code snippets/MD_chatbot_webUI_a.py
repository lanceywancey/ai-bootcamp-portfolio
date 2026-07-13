import os
from groq import Groq
import gradio as gr

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Markdown file used as simple memory storage
FILE = "memory.md"


def load_memory():
    try:
        # Read all previous conversations from file
        with open(FILE, "r") as f:
            return f.read()
    except:
        # Return empty memory if file doesn't exist yet
        return ""


def save_memory(prompt, reply):
    # Append latest conversation into markdown file
    with open(FILE, "a") as f:
        f.write(f"User: {prompt}\n")
        f.write(f"Bot: {reply}\n\n")


def chat_bot(prompt, history):
    # Load previous memory
    memory_text = load_memory()

    # Send old memory + current prompt to LLM
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"Previous memory:\n{memory_text}"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.1-8b-instant"
    )

    reply = response.choices[0].message.content

    # Save current conversation for future use
    save_memory(prompt, reply)

    return reply


# Launch chatbot UI
gr.ChatInterface(
    fn=chat_bot,
    title="Markdown Memory Bot"
).launch()