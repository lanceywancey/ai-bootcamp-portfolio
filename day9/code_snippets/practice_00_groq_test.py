"""
Practice 00: Groq Connection Test
==================================
Goal: Verify that your Groq API key is set up correctly
      and that you can call an LLM BEFORE adding RAG complexity.

Fix API key issues here first — before PDF/RAG debugging!
"""

from dotenv import load_dotenv
from groq import Groq
import os

# Load .env file if it exists
load_dotenv()

# Check the key is present
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found!\n"
        "Set it in your terminal:\n"
        "  macOS/Linux: export GROQ_API_KEY='your-key-here'\n"
        "  Windows CMD: set GROQ_API_KEY=your-key-here\n"
        "  Windows PS:  $env:GROQ_API_KEY='your-key-here'\n"
        "Or create a .env file with: GROQ_API_KEY=your-key-here"
    )

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",        # Fast, free model on Groq
    messages=[
        {"role": "user", "content": "Explain RAG in one sentence."}
    ],
    temperature=0.2,
)

print("✅ Groq connection successful!")
print("-" * 40)
print(response.choices[0].message.content)
