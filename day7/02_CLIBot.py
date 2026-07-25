import sys
sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252, which can't print emoji

from litellm import completion

# Configuration
MODEL = "ollama/llama3:latest"  # Change this to whatever model you have pulled locally
OLLAMA = "http://localhost:11434"

def main():
    # Initialize session state (conversation history)
    # The system prompt sets the behavior of the AI
    messages = [
        {
            'role': 'system',
            'content': 'You are a helpful, witty, and concise AI assistant.'
        }
    ]

    print("Local Ollama Chatbot Initialized")
    print("Type your question and press Enter. Type 'exit' or 'quit' to end.")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye! Thanks for chatting.")
                break
            if not user_input:
                continue

            messages.append({'role': 'user', 'content': user_input})

            response = completion(
                model=MODEL,
                messages=messages,
                api_base=OLLAMA,
                stream=True
            )

            print("AI: ", end="", flush=True)
            full_response = ""
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
                    full_response += content
            print()

            messages.append({'role': 'assistant', 'content': full_response})

        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye!")
            break

if __name__ == "__main__":
    main()