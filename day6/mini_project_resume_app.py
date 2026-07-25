import streamlit as st

st.sidebar.title("Your Info")
name = st.sidebar.text_input("Name")

st.title("Simple Resume App")

if "upload_count" not in st.session_state:
    st.session_state.upload_count = 0
if "last_file_id" not in st.session_state:
    st.session_state.last_file_id = None

resume = st.file_uploader("Upload your resume", type=["pdf", "txt"])

if resume:
    if resume.file_id != st.session_state.last_file_id:
        st.session_state.upload_count += 1
        st.session_state.last_file_id = resume.file_id

        st.snow()
        st.balloons()
        
    st.success(f"Hello {name}, we received: {resume.name}")

    st.subheader("Preview")

    if resume.type == "application/pdf":
        st.pdf(resume, height=700)

    elif resume.type == "text/plain":
        text_content = resume.getvalue().decode("utf-8")
        st.text_area("Text preview",value=text_content,height=500,disabled=True)

st.metric("Times uploaded this session", st.session_state.upload_count)