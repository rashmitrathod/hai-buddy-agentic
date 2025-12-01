import streamlit as st
import requests
from streamlit_mic_recorder import mic_recorder, speech_to_text
import base64

BACKEND_URL = "http://localhost:8899"

st.set_page_config(page_title="HAI Buddy", layout="wide")

st.title("HAI Buddy — Your Conversational Learning Assistant")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.write("Speak or type your question:")

# --------------------------
# VOICE INPUT SECTION
# --------------------------

st.subheader("Voice Input")

audio = mic_recorder(
    start_prompt="Start Talking",
    stop_prompt="Stop",
    format="wav"
)

if audio:
    st.success("Audio captured. Sending to Speech-to-Text…")

    st.audio(audio["bytes"], format="audio/wav")

    # Send to /stt
    files = {"file": ("audio.wav", audio["bytes"], "audio/wav")}
    stt_resp = requests.post(f"{BACKEND_URL}/stt", files=files)

    if stt_resp.status_code == 200:
        transcript = stt_resp.json()["transcript"]
        st.write(f"**You said:** {transcript}")

        # Send transcript to /ask
        ask_resp = requests.post(f"{BACKEND_URL}/ask", json={"question": transcript})

        if ask_resp.status_code == 200:
            data = ask_resp.json()
            st.session_state.chat_history.append(
                {"user": transcript, "buddy": data.get("answer"), "audio": data.get("audio_url")}
            )
            st.success("HAI Buddy responded!")

# --------------------------
# TEXT INPUT SECTION
# --------------------------

st.subheader("Type Your Question")

question = st.text_input("Ask your question to HAI Buddy")

if st.button("Send"):
    if question.strip():
        resp = requests.post(f"{BACKEND_URL}/ask", json={"question": question})
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.chat_history.append(
                {"user": question, "buddy": data.get("answer"), "audio": data.get("audio_url")}
            )
            st.success("HAI Buddy responded!")
    else:
        st.warning("Please enter a question.")

# --------------------------
# CHAT HISTORY
# --------------------------

st.subheader("Conversation History")

for chat in st.session_state.chat_history:
    st.markdown(f"**You:** {chat['user']}")
    st.markdown(f"**HAI Buddy:** {chat['buddy']}")

    if chat.get("audio"):
        st.audio(chat["audio"], format="audio/mp3")