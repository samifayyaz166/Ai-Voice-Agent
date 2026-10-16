import os
import hashlib

import streamlit as st
from dotenv import load_dotenv

from src.ai_brain import get_ai_response
from src.text_to_speech import generate_speech
from src.speech_to_text import transcribe_audio

from src.memory import (
    initialize_memory,
    add_message,
    get_conversation_history,
    clear_memory,
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Voice Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    try:
        API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        API_KEY = None

initialize_memory()

VOICE_NAME = "en-US-JennyNeural"

# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "processed_audio_id": None,
    "recorder_version": 0,
    "user_audio": {},
    "reply_audio": {},
    "autoplay_index": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: #000000;
        color: #ffffff;
    }
    section[data-testid="stSidebar"] {
        background: #0b0b0b;
        border-right: 1px solid #252525;
    }
    section[data-testid="stSidebar"] * { color: #ffffff; }
    .app-header { text-align: center; padding: 25px 0 20px 0; }
    .app-title { font-size: 32px; font-weight: 700; color: #ffffff; }
    .app-subtitle { color: #999999; font-size: 14px; margin-top: 5px; }
    .voice-heading {
        text-align: center; color: #bbbbbb; font-size: 17px;
        margin-top: 25px; margin-bottom: 10px;
    }
    [data-testid="stChatMessage"] { background: transparent !important; }
    [data-testid="stChatMessageContent"] { color: #ffffff !important; }
    [data-testid="stChatInput"] {
        background: #171717 !important;
        border: 1px solid #333333 !important;
        border-radius: 14px !important;
    }
    [data-testid="stChatInput"] textarea { color: #ffffff !important; }
    .stButton > button {
        background: #202020; color: #ffffff;
        border: 1px solid #444444; border-radius: 10px;
    }
    audio { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🎙️ AI Voice Agent")
    st.caption("Your intelligent voice assistant")
    st.divider()

    st.markdown("### System Status")

    if API_KEY:
        st.success("AI Brain: Connected")
    else:
        st.error("AI Brain: API key missing")

    st.info("Speech Recognition: Groq Whisper")
    st.info("Voice Engine: Edge TTS")
    st.info("Microphone: Streamlit")

    st.divider()
    st.markdown("### Conversation")
    st.caption(f"Messages: {len(st.session_state.messages)}")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        clear_memory()
        st.session_state.user_audio = {}
        st.session_state.reply_audio = {}
        st.session_state.autoplay_index = None
        st.session_state.processed_audio_id = None
        st.session_state.recorder_version += 1
        st.rerun()

# ============================================================
# API KEY CHECK
# ============================================================

if not API_KEY:
    st.error("GROQ_API_KEY is missing. Please add it to your .env file.")
    st.stop()

# ============================================================
# AI RESPONSE
# ============================================================


def generate_ai_response(user_message, user_audio=None):

    user_message = user_message.strip()

    if not user_message:
        return False

    try:
        user_index = len(st.session_state.messages)

        add_message("user", user_message)

        if user_audio:
            st.session_state.user_audio[user_index] = user_audio

        history = get_conversation_history()
        previous_history = history[:-1]

        response = get_ai_response(
            user_message=user_message,
            conversation_history=previous_history,
            api_key=API_KEY,
        )

        response = (response or "").strip()

        if not response:
            response = "Sorry, I could not generate an answer."

        assistant_index = len(st.session_state.messages)

        add_message("assistant", response)

        try:
            audio_data = generate_speech(response, voice=VOICE_NAME)

            if audio_data:
                st.session_state.reply_audio[assistant_index] = audio_data
                st.session_state.autoplay_index = assistant_index

        except Exception as error:

            import traceback
            traceback.print_exc()
            st.error(f"Voice Generation Error: {error}")
        return True

    except Exception as error:
        st.error(f"AI Error: {error}")
        return False


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">🎙️ AI Voice Agent</div>
        <div class="app-subtitle">Talk naturally with your AI assistant</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# CHAT HISTORY
# ============================================================

autoplay_index = st.session_state.autoplay_index

for index, message in enumerate(st.session_state.messages):

    role = message["role"]
    avatar = "🧑" if role == "user" else "🤖"

    with st.chat_message(role, avatar=avatar):

        st.markdown(message["content"])

        if role == "user" and index in st.session_state.user_audio:
            st.caption("🎧 Your recorded voice")
            st.audio(
                st.session_state.user_audio[index],
                format="audio/wav",
            )

        if role == "assistant" and index in st.session_state.reply_audio:
            st.caption("🔊 Agent voice (replay anytime)")
            st.audio(
                st.session_state.reply_audio[index],
                format="audio/mpeg",
                autoplay=(index == autoplay_index),
            )

st.session_state.autoplay_index = None

# ============================================================
# TEXT INPUT
# ============================================================

user_text = st.chat_input("Message your AI assistant...")

if user_text and user_text.strip():

    with st.spinner("🤖 AI is thinking..."):
        success = generate_ai_response(user_text)

    if success:
        st.rerun()

# ============================================================
# VOICE SECTION
# ============================================================

st.markdown(
    '<div class="voice-heading">🎙️ Speak with your AI assistant</div>',
    unsafe_allow_html=True,
)

st.caption("Click the microphone, speak your question, then stop recording.")

audio_value = st.audio_input(
    "🎙️ Record your voice",
    sample_rate=16000,
    key=f"voice_{st.session_state.recorder_version}",
)

# ============================================================
# AUDIO PROCESSING
# ============================================================

if audio_value is not None:

    audio_bytes = audio_value.getvalue()

    if not audio_bytes:
        st.error("No audio was received from the microphone.")

    else:
        audio_id = hashlib.sha256(audio_bytes).hexdigest()

        if audio_id != st.session_state.processed_audio_id:

            st.session_state.processed_audio_id = audio_id

            transcript = ""

            with st.spinner("🎧 Converting your voice to text..."):
                try:
                    transcript = transcribe_audio(
                        audio_bytes=audio_bytes,
                        api_key=API_KEY,
                    ).strip()
                except Exception as error:
                    st.error(f"Speech Recognition Error: {error}")

            if transcript:

                with st.spinner("🤖 AI is thinking..."):
                    success = generate_ai_response(
                        transcript,
                        user_audio=audio_bytes,
                    )

                if success:
                    st.session_state.recorder_version += 1
                    st.rerun()

            else:
                st.warning(
                    "I could not hear any clear speech. "
                    "Please speak a bit louder and try again."
                )

