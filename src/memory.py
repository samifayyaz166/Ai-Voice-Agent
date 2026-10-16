import streamlit as st


def initialize_memory():

    if "messages" not in st.session_state:
        st.session_state.messages = []


def add_message(role: str, content: str):

    st.session_state.messages.append({
        "role": role,
        "content": content
    })


def get_conversation_history():

    return st.session_state.messages.copy()


def clear_memory():

    st.session_state.messages = []