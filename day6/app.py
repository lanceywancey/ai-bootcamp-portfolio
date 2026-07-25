import streamlit as st


# st.title("My First AI App")
# name = st.text_input("Enter your name")

# if st.button("Click Me"):
#     st.write(f"Hello {name} 👋")

# st.write("Plain text")
# st.write({"a": 1, "b": 2})     # renders as an expandable object
# # st.write(some_dataframe)        # renders as a table

# st.markdown("## Heading **bold** and *italic*")

# st.success("Model loaded!")   # green
# st.error("Invalid .pkl file") # red
# st.info("Tip: ...")           # blue
# st.warning("Careful ...")     # yellow

st.sidebar.title("Settings")
st.sidebar.markdown("Please enter your username")
username = st.sidebar.text_input("Enter Username", value="Admin")
role = st.sidebar.selectbox("Role", ["Student", "Instructor", "Admin"])

st.title(f"Welcome, {username}! ({role})")

left_col, right_col = st.columns([3, 1])   # 3:1 width ratio

with left_col:
    st.header("Main Content")
    st.write("This is the primary area for your data or chat interface.")
    st.info("Notice how this column stays wide while the other is narrow.")

with right_col:
    st.header("Stats")
    st.metric(label="System Status", value="Online")
    st.metric(label="Latency", value="12ms")
    

import streamlit as st

uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "txt"])

if uploaded_file:                       # None until the user uploads
    st.success("File uploaded!")
    st.write(f"The file name is: {uploaded_file.name}")

# if uploaded_file:
#     text = uploaded_file.read().decode("utf-8")   # plain text files
#     # or: pandas.read_csv(uploaded_file)
#     # or: PIL.Image.open(uploaded_file)

st.title("The Persistent Counter")
count = 0                                        # normal variable — resets every rerun

if "count" not in st.session_state:              # init guard — runs once per session
    st.session_state["count"] = 0

def increment_counter():
    st.session_state["count"] += 1

def reset_counter():
    st.session_state["count"] = 0

col1, col2 = st.columns(2)
with col1:
    if st.button("Add +1"):
        count += 1
        increment_counter()
with col2:
    if st.button("Reset"):
        count = 0
        reset_counter()

st.write(f"Current Count (with Session State): **{st.session_state['count']}**")
st.write(f"Current Count (without Session State): **{count}**")   # never exceeds 1

# if user_input := st.chat_input("Say something"):
#     with st.chat_message("user"):
#         st.markdown(user_input)
#     with st.chat_message("assistant"):
#         st.markdown(f"You said: {user_input}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Type your message..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    reply = f"Echo: {user_input}"          # Later: replace with a real LLM call
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

st.title("Scene Object Manager")

if "scene_objects" not in st.session_state:
    st.session_state.scene_objects = []
if "next_id" not in st.session_state:
    st.session_state.next_id = 1

st.header("Add a new object")
name = st.text_input("Name")
x = st.number_input("X", value=0.0)
y = st.number_input("Y", value=0.0)
z = st.number_input("Z", value=0.0)

if st.button("Add Object"):
    if not name:
        st.warning("Name is required.")
    else:
        st.session_state.scene_objects.append({
            "id": st.session_state.next_id,
            "name": name,
            "position": [x, y, z],
        })
        st.session_state.next_id += 1

st.header("Current objects")
if not st.session_state.scene_objects:
    st.info("No objects yet.")
for obj in st.session_state.scene_objects:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"**#{obj['id']} {obj['name']}** — position {obj['position']}")
    with col2:
        if st.button("Delete", key=f"delete_{obj['id']}"):
            st.session_state.scene_objects = [
                o for o in st.session_state.scene_objects if o["id"] != obj["id"]
            ]
            st.rerun()