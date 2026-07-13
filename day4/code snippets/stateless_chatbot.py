import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

# Create connection to Groq API
# Make sure your GROQ_API_KEY is stored in environment variables
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

    # Return the AI response text
    return chat_completion.choices[0].message.content


# Keep chatbot running until user stops program manually
while True:
    # Get user input from terminal
    user = input("You: ")

    # Generate chatbot response
    reply = chat_bot(user)

    # Print response
    print("Bot:", reply)