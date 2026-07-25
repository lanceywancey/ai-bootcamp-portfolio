from litellm import completion
import config

def get_ai_response_stream(messages):
    """
    Sends the list of messages to the local Ollama instance via litellm.
    Returns a raw streaming completion response.
    """
    return completion(
        model=f"ollama/{config.MODEL_NAME}",
        messages=messages,
        api_base=config.OLLAMA_API_BASE,
        stream=True
    )

def parse_stream_chunks(raw_stream):
    """
    A generator function that yields text content chunk-by-chunk.
    This formats the raw litellm stream response into a clean text stream for UIs.
    """
    for chunk in raw_stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content