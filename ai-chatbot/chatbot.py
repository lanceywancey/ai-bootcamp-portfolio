from litellm import completion
from mem0 import Memory

MODEL = "gemma4:e2b"
MODEL_PATH = f"ollama/{MODEL}"
OLLAMA = "http://localhost:11434"
USER_ID = "student1"

config = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "chatbot_memory",
            "path": "./chroma_db"
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
            "ollama_base_url": OLLAMA
        }
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": MODEL,
            "ollama_base_url": OLLAMA
        }
    }
}

memory = Memory.from_config(config)

def chat(user_message, history):
    memory_results = memory.search(
        query=user_message,
        filters={"user_id": USER_ID}
    )

    system_prompt = f"""
You are a helpful chatbot.

Relevant memories about the user:
{memory_results}
"""

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": user_message
    })

    response = completion(
        model=MODEL_PATH,
        messages=messages,
        api_base=OLLAMA
    )

    assistant_reply = response.choices[0].message.content

    memory.add(user_message, user_id=USER_ID)
    memory.add(assistant_reply, user_id=USER_ID)

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


if __name__ == "__main__":
    print("Chatbot ready")

    history = []

    while True:
        user_message = input("You: ").strip()

        if user_message.lower() in ["quit", "exit"]:
            break
        if not user_message:
            continue

        reply = chat(user_message, history)
        print("Bot:", reply)