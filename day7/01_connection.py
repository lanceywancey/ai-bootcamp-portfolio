import sys
sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252, which can't print emoji

from litellm import completion

MODEL = "ollama/gemma3:4b"
OLLAMA = "http://localhost:11434"

response = completion(
    model = MODEL,
    messages = [{"role": "user", "content": "Say hello in one sentence"}],
    api_base = OLLAMA,
)

print(response.choices[0].message.content)