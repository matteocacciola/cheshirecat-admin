import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.utils import show_overlay_spinner, build_client_configuration


def login_page():
    st.title("Login Page")

    # Render login form
    with st.form(key="login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if not st.form_submit_button(label="Login"):
            return

        if not username or not password:
            st.error("Please enter both username and password.")
            return

        spinner_container = show_overlay_spinner(f"Authenticating {username}...")
        try:
            client = CheshireCatClient(build_client_configuration())
            token_response = client.admins.token(username, password)
            token = token_response.access_token

            st.session_state["token"] = token
            st.toast("Login successful!", icon="✅")

            spinner_container.empty()

            time.sleep(1)  # Wait for a moment before rerunning
            st.rerun()
        except Exception as e:
            spinner_container.empty()
            st.error(f"Error during authentication: {e}")
            return
