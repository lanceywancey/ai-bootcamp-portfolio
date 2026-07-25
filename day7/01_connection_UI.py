import streamlit as st
from litellm import completion

# --- CONFIG ---
OLLAMA = "http://localhost:11434"

st.title("🔌 LLM Connection Tester")

# --- MODEL SELECTION ---
# List only models you've actually pulled locally — check with `ollama list`.
model_option = st.selectbox(
    "Select Model",
    ["gemma3:4b", "llama3:latest"]
)

input = "Are you ready to chat?"

MODEL = f"ollama/{model_option}"

# --- TEST BUTTON ---
if st.button("Test Connection"):
    try:
        response = completion(
            model=MODEL,
            messages=[{"role": "user", "content": input}],
            api_base=OLLAMA,
        )

        reply = response.choices[0].message.content

        st.success("Connection successful!")
        st.write("### Model Response:")
        st.write(reply)

    except Exception as e:
        st.error("Connection failed!")
        st.write(str(e))