import json
from typing import Dict, Any, List
from slugify import slugify
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient, Configuration
from cheshirecat_python_sdk.models.api.factories import FactoryObjectSettingOutput
from streamlit_js_eval import set_cookie

from app.constants import DEFAULT_SYSTEM_KEY
from app.env import get_env, get_env_bool


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


def build_agents_options_select(cookie_me: Dict | None, excluded_agents: List[str] | None = None) -> Dict[str, str]:
    if cookie_me:  # login by credentials
        agents = [agent["agent_name"] for agent in cookie_me.get("agents", [])]
    else:  # login by API key
        client = CheshireCatClient(build_client_configuration())
        agents = client.utils.get_agents()

    return {
        agent: slugify(agent) for agent in agents if agent not in (excluded_agents or [])
    }


def build_agents_select(k: str, cookie_me: Dict | None):
    if st.session_state.get("agent_id") is not None:
        return  # already selected

    # Navigation
    agent_options = build_agents_options_select(cookie_me)
    if len(agent_options) == 0:
        return

    menu_options = {"(Select an Agent)": None} | agent_options
    choice = st.selectbox("Agents", menu_options, key=f"agent_select_{k}")
    if menu_options[choice] is None:
        st.info("Please select an agent to manage.")
        st.session_state.pop("agent_id", None)
        return

    st.session_state["agent_id"] = choice


def build_users_select(k: str, agent_id: str, cookie_me: Dict | None):
    if st.session_state.get("user_id") is not None:
        return  # already selected

    if cookie_me:  # login by credentials
        agent_match = next((agent for agent in cookie_me.get("agents", []) if agent.get("agent_name") == agent_id), None)
        if not agent_match:
            st.error("Agent not found in user data.")
            return
        st.session_state["user_id"] = agent_match.get("user", {}).get("id")
        return

    client = CheshireCatClient(build_client_configuration())
    users = client.users.get_users(agent_id)

    # Navigation
    menu_options = {"(Select an User)": None} | {user.username: user.id for user in users}
    choice = st.selectbox("Users", menu_options, key=f"user_select_{k}")
    if menu_options[choice] is None:
        st.info("Please select an user to manage.")
        st.session_state.pop("user_id", None)
        return

    st.session_state["user_id"] = menu_options[choice]


def build_conversations_select(k: str, agent_id: str, user_id: str):
    client = CheshireCatClient(build_client_configuration())
    conversations = client.conversation.get_conversations(agent_id, user_id)

    if not conversations:
        st.info("No conversations found for this user.")
        st.session_state.pop("conversation_id", None)
        return

    # Navigation
    menu_options = (
        {"(Select a Conversation)": None} |
        {conversation.name: conversation.chat_id for conversation in conversations}
    )
    choice = st.selectbox("Conversations", menu_options, key=f"conversation_select_{k}")
    if menu_options[choice] is None:
        st.info("Please select a conversation to manage.")
        st.session_state.pop("conversation_id", None)
        return

    st.session_state["conversation_id"] = menu_options[choice]


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


def build_client_configuration():
    return Configuration(
        host=get_env("CHESHIRE_CAT_API_HOST").replace("https://", "").replace("http://", ""),
        port=int(get_env("CHESHIRE_CAT_API_PORT")),
        auth_key=st.session_state.get("token"),
        secure_connection=get_env_bool("CHESHIRE_CAT_API_SECURE_CONNECTION"),
    )


def render_json_form(data: Dict, prefix: str = "") -> Dict:
    """Recursively render form fields for JSON data."""
    def infer_type(v: Any) -> str:
        if isinstance(v, bool):
            return "boolean"
        if isinstance(v, int):
            return "integer"
        if isinstance(v, float):
            return "float"
        if isinstance(v, str):
            return "string"
        if isinstance(v, (list, dict)):
            return "json"
        return "string"

    def create_input_field(v) -> Any:
        field_type = infer_type(v)
        if field_type == "boolean":
            return st.checkbox(key, value=v, key=path)
        if field_type == "integer":
            return st.number_input(key, value=v, step=1, key=path)
        if field_type == "float":
            return st.number_input(key, value=v, step=0.1, format="%.2f", key=path)
        if field_type == "string":
            return st.text_input(key, value=v, key=path)
        if field_type == "json":
            # For nested structures, show as editable JSON text
            json_str = json.dumps(v, indent=2)
            r = st.text_area(key, value=json_str, height=100, key=path)
            try:
                return json.loads(r)
            except:
                st.error(f"Invalid JSON in field '{key}'")
                return v
        return v

    result = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict) and not any(isinstance(v, (list, dict)) for v in value.values()):
            # Simple dict - render fields inline
            st.subheader(key)
            result[key] = render_json_form(value, path)
        else:
            # Render a single field
            result[key] = create_input_field(value)

    return result


def has_access(resource: str, required_role: str | None, cookie_me: Dict | None, only_admin: bool | None = False) -> bool:
    """Check if the logged-in user has the required role."""
    if not cookie_me: # logged by API key
        return True

    agent_id = st.session_state.get("agent_id")
    if not agent_id:
        return False

    if only_admin and agent_id != DEFAULT_SYSTEM_KEY:
        return False

    try:
        # in cookie_me.agents find the one with agent_id
        agent_match = next((agent for agent in cookie_me.get("agents", []) if agent.get("agent_name") == agent_id), None)
        if not agent_match:
            return False

        user_permissions = agent_match.get("user", {}).get("permissions", {}).get(resource, [])
        return required_role in user_permissions if required_role else len(user_permissions) > 0
    except json.JSONDecodeError:
        return False


def clear_auth_cookies():
    """Clear authentication-related cookies."""
    set_cookie("token", "", duration_days=-1)
    set_cookie("me", "", duration_days=-1)


def is_system_agent_selected() -> bool:
    return st.session_state.get("agent_id") == DEFAULT_SYSTEM_KEY
