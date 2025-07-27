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
        k: v.get("default") for k, v in factory.scheme.get("properties", {}).items()
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
