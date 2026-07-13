import os
from groq import Groq
import gradio as gr

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def chat_bot(prompt, history):
    # ChatInterface automatically provides:
    # prompt  = current user message
    # history = previous UI conversation
    
    # For now, we ignore history
    # This means the chatbot is still stateless
    # It only sees the latest user message
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.1-8b-instant"
    )

    # Return AI response
    return chat_completion.choices[0].message.content


# ChatInterface creates a real chatbot-style UI
# Unlike gr.Interface:
# - shows chat bubbles
# - keeps conversation visible on screen
# - passes history into the function
gr.ChatInterface(
    fn=chat_bot,
    title="Stateless Chatbot Demo",
    description="This UI shows previous messages, but the model only receives the latest input."
).launch()