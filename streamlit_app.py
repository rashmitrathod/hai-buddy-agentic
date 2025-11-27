import streamlit as st
import requests

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Page title
st.title("HAI Buddy: Ask Your Digital Friend")

# User input
question = st.text_input("Ask your question to HAI Buddy:", "")

if st.button("Send") and question.strip():
    # Send POST request to backend
    try:
        response = requests.post(
            "http://localhost:8899/ask",
            json={"question": question}
        )
        if response.status_code == 200:
            data = response.json()
            # Append to chat history
            st.session_state.chat_history.append({
                "user": question,
                "buddy": data.get("answer"),
                "audio": data.get("audio_url")
            })
        else:
            st.error(f"Backend error: {response.status_code}")
    except Exception as e:
        st.error(f"Request failed: {e}")

# Render chat history
if st.session_state.chat_history:
    st.markdown("---")
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        st.markdown(f"**Buddy:** {chat['buddy']}")
        if chat.get("audio"):
            st.audio(chat['audio'])
        st.markdown("---")