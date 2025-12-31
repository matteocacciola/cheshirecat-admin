from typing import Dict

import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient
from cheshirecat_python_sdk.models.dtos import Message

from app.constants import INTRO_MESSAGE
from app.utils import build_agents_select, build_users_select, build_client_configuration, has_access


def chat(cookie_me: Dict | None):
    st.header("Chat with the CheshireCat")

    if not has_access("CHAT", "WRITE", cookie_me):
        st.error("You do not have permission to access the chat functionality.")
        return

    build_agents_select("chat", cookie_me)
    if not (agent_id := st.session_state.get("agent_id")):
        return

    build_users_select("chat", agent_id, cookie_me)
    if not (user_id := st.session_state.get("user_id")):
        return

    st.session_state["chat_id"] = st.session_state.get("chat_id")

    st.session_state["messages"] = st.session_state.get("messages", [])
    if not st.session_state["messages"] and INTRO_MESSAGE:
        st.session_state["messages"].append({
            "role": "assistant",
            "content": INTRO_MESSAGE,
        })

    client = CheshireCatClient(build_client_configuration())

    user_message = st.chat_input(placeholder="Type your message here...")
    if user_message:
        try:
            response = client.message.send_http_message(
                Message(text=user_message), agent_id=agent_id, user_id=user_id, chat_id=st.session_state["chat_id"],
            )

            st.session_state["messages"].append({
                "role": "user",
                "content": user_message,
            })

            st.session_state["messages"].append({
                "role": "assistant",
                "content": response.message.text,
            })
            st.session_state["chat_id"] = response.chat_id
        except Exception as e:
            st.toast(f"Error sending message: {e}", icon="❌")

    st.write("###     Conversation History")
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
