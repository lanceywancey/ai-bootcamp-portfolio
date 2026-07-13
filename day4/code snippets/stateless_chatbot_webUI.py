import os
from groq import Groq
import gradio as gr

# Connect to Groq API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def chat_bot(prompt):
    # Send user message to the LLM
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


# Create simple web interface using Gradio
# input: textbox
# output: chatbot response
gr.Interface(
    fn=chat_bot,
    inputs="text",
    outputs="text"
).launch()