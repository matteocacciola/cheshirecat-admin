from typing import Dict, Any
from slugify import slugify
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient
from cheshirecat_python_sdk.models.api.factories import FactoryObjectSettingOutput

from app.constants import CLIENT_CONFIGURATION


def get_factory_settings(factory: FactoryObjectSettingOutput, is_selected: bool) -> Dict[str, Any]:
    """
    Get the settings of a factory instance.

    Args:
        factory: The factory instance to get settings from.
        is_selected: A boolean indicating if the factory is selected.

    Returns:
        A dictionary containing the settings of the factory.
    """
    return factory.value if is_selected else {
        k: v.get("default") for k, v in factory.scheme.get("properties", {}).items() if isinstance(v, dict)
    }


def build_agents_select():
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    agents = client.admins.get_agents()

    # Sidebar navigation
    menu_options = {"(Select an Agent)": None} | {agent: slugify(agent) for agent in agents}
    choice = st.selectbox("Agents", menu_options)
    if menu_options[choice] is None:
        st.info("Please select an agent to manage.")
        st.session_state.pop("agent_id", None)
    else:
        st.session_state["agent_id"] = choice


def build_users_select(agent_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    users = client.users.get_users(agent_id)

    # Navigation
    menu_options = {"(Select an User)": None} | {user.username: user.id for user in users}
    choice = st.selectbox("Users", menu_options)
    if menu_options[choice] is None:
        st.info("Please select an user to manage.")
        st.session_state.pop("user_id", None)
    else:
        st.session_state["user_id"] = menu_options[choice]


def run_toast():
    if st.session_state.get("toast") is None:
        return
    toast = st.session_state["toast"]
    st.toast(toast["message"], icon=toast["icon"])
    st.session_state.pop("toast", None)


def show_overlay_spinner(message="Processing..."):
    """Show a full-page overlay spinner"""
    spinner_container = st.empty()
    with spinner_container.container():
        st.markdown(f"""
        <style>
        .overlay-spinner {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-size: 18px;
        }}
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
            margin-right: 15px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        <div class="overlay-spinner">
            <div class="spinner"></div>
            <div>{message}</div>
        </div>
        """, unsafe_allow_html=True)
    return spinner_container