import streamlit as st
import requests

API_URL = "http://127.0.0.1:5000"

st.title("Scene Object Manager")

st.header("Current objects")
try:
    response = requests.get(f"{API_URL}/objects")
    objects = response.json()
    if not objects:
        st.info("No objects yet.")
    for obj in objects:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**#{obj['id']} {obj['name']}** — position {obj['position']}")
        with col2:
            if st.button("Delete", key=f"delete_{obj['id']}"):
                requests.delete(f"{API_URL}/objects/{obj['id']}")
                st.rerun()
except requests.exceptions.ConnectionError:
    st.error("Could not reach the Flask API. Is app.py running?")
    
st.header("Add a new object")
name = st.text_input("Name")
x = st.number_input("X", value=0.0)
y = st.number_input("Y", value=0.0)
z = st.number_input("Z", value=0.0)

if st.button("Add Object"):
    if not name:
        st.warning("Name is required.")
    else:
        try:
            response = requests.post(
                f"{API_URL}/objects",
                json={"name": name, "position": [x, y, z]},
            )
            if response.status_code == 201:
                st.success(f"Added '{name}'")
                st.rerun()
            else:
                st.error(f"Server returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("Could not reach the Flask API. Is app.py running?")