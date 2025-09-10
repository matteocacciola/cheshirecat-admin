import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient
from cheshirecat_python_sdk.models.dtos import Message

from app.constants import INTRO_MESSAGE
from app.utils import build_agents_select, build_users_select, build_client_configuration


def chat():
    st.header("Chat with the CheshireCat")

    build_agents_select()
    if "agent_id" not in st.session_state:
        return

    agent_id = st.session_state.agent_id
    build_users_select(agent_id)

    if "user_id" not in st.session_state:
        return

    user_id = st.session_state.user_id
    st.session_state.messages = st.session_state.get("messages", [])
    if not st.session_state.messages and INTRO_MESSAGE:
        st.session_state.messages.append({
            "role": "assistant",
            "content": INTRO_MESSAGE,
        })

    client = CheshireCatClient(build_client_configuration())

    user_message = st.chat_input(placeholder="Type your message here...")
    if user_message:
        try:
            response = client.message.send_http_message(
                Message(text=user_message), agent_id=agent_id, user_id=user_id
            )

            st.session_state.messages.append({
                "role": "user",
                "content": user_message,
            })

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.content,
            })
        except Exception as e:
            st.toast(f"Error sending message: {e}", icon="❌")

    st.write("###     Conversation History")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
