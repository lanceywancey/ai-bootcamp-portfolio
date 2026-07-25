import streamlit as st
from litellm import completion

st.set_page_config(page_title="Ollama Chatbot", page_icon="🤖", layout="centered")

MODEL = "ollama/llama3:latest"  # Change this to whatever model you have pulled locally
OLLAMA = "http://localhost:11434"

st.title("🤖 Local Ollama Chatbot")
st.caption(f"Running locally with model: **{MODEL}**")
st.markdown("---")

# 1. Session state replaces the CLI's plain `messages` list
if "messages" not in st.session_state:
    st.session_state.messages = [
        {'role': 'system', 'content': 'You are a helpful, witty, and concise AI assistant.'}
    ]

# 2. Render history (skip the system message — the user never sees the prompt)
for msg in st.session_state.messages:
    if msg['role'] != 'system':
        with st.chat_message(msg['role']):
            st.write(msg['content'])

# 3. Handle new input
if user_input := st.chat_input("Type your question here..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({'role': 'user', 'content': user_input})

    # 4. Call litellm and stream the reply into the assistant bubble
    with st.chat_message("assistant"):
        try:
            response_stream = completion(
                model=MODEL,
                messages=st.session_state.messages,
                api_base=OLLAMA,
                stream=True
            )

            def stream_parser():
                for chunk in response_stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content

            full_response = st.write_stream(stream_parser())
            st.session_state.messages.append({'role': 'assistant', 'content': full_response})

        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Please ensure your local Ollama server is running (usually at http://localhost:11434).")