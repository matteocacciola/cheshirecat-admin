import json
from typing import Dict, Any, List, Tuple
from grinning_cat_python_sdk.models.api.nested.plugins import PluginSettingsOutput
from slugify import slugify
import streamlit as st
from grinning_cat_python_sdk import GrinningCatClient, Configuration
from grinning_cat_python_sdk.models.api.factories import FactoryObjectSettingOutput
from streamlit_js_eval import set_cookie

from app.constants import DEFAULT_SYSTEM_KEY
from app.env import get_env, get_env_bool


def get_settings(
    settings: PluginSettingsOutput, is_selected: bool
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if is_selected:
        return settings.value, {}

    if not settings.scheme:
        return {}, {}

    values = {}
    types = {}
    for k, v in settings.scheme.properties.items():
        values[k] = v.default
        types[k] = v.type
    return values, types


def get_factory_settings(
    factory: FactoryObjectSettingOutput, is_selected: bool
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Get the settings of a factory instance.

    Args:
        factory: The factory instance to get settings from.
        is_selected: A boolean indicating if the factory is selected.

    Returns:
        A tuple containing two dictionaries:
            - The first dictionary contains the current values of the factory settings.
            - The second dictionary contains the types of the factory settings.
    """
    def get_type():
        if "type" in v:
            return v["type"]
        if "anyOf" in v:
            tmp_types = [t.get("type") for t in v["anyOf"] if "type" in t and t.get("type") != "null"]
            return tmp_types[0] if tmp_types else "string"
        return "string"

    if is_selected:
        return factory.value, {}

    values = {}
    types = {}
    for k, v in factory.scheme.get("properties", {}).items():
        if isinstance(v, dict):
            values[k] = v.get("default")
            types[k] = get_type()
    return values, types


def build_agents_options_select(cookie_me: Dict | None, excluded_agents: List[str] | None = None) -> Dict[str, str]:
    if cookie_me:  # login by credentials
        agents = [agent["agent_name"] for agent in cookie_me.get("agents", [])]
    else:  # login by API key
        client = GrinningCatClient(build_client_configuration())
        agents = [agent.agent_id for agent in client.utils.get_agents()]

    return {
        agent: slugify(agent) for agent in agents if agent not in (excluded_agents or [])
    }


def build_agents_select(k: str, cookie_me: Dict | None, force_system_agent: bool = False):
    if st.session_state.get("agent_id") is not None and cookie_me is not None:
        return  # already selected and logged by credentials

    # Navigation
    agent_options = build_agents_options_select(cookie_me)
    if force_system_agent and DEFAULT_SYSTEM_KEY not in agent_options:
        agent_options = {DEFAULT_SYSTEM_KEY: slugify(DEFAULT_SYSTEM_KEY)} | agent_options
    if len(agent_options) == 0:
        st.info("No agents found. Please create an agent first.")
        return

    menu_options = {"(Select an Agent)": None} | agent_options
    choice = st.selectbox("Agents", menu_options, key=f"agent_select_{k}")
    if menu_options[choice] is None:
        st.info("Please select an agent to manage.")
        st.session_state.pop("agent_id", None)
        if not cookie_me:
            st.session_state.pop("user_id", None)
            st.session_state.pop("conversation_id", None)
        return

    st.session_state["agent_id"] = choice


def build_users_select(k: str, agent_id: str, cookie_me: Dict | None):
    if st.session_state.get("user_id") is not None and cookie_me is not None:
        return  # already selected

    if cookie_me:  # login by credentials
        agent_match = next((agent for agent in cookie_me.get("agents", []) if agent.get("agent_name") == agent_id), None)
        if not agent_match:
            st.error("Agent not found in user data.")
            return
        st.session_state["user_id"] = agent_match.get("user", {}).get("id")
        return

    client = GrinningCatClient(build_client_configuration())
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
    client = GrinningCatClient(build_client_configuration())
    conversations = client.conversation.get_conversations(agent_id, user_id)

    if not conversations:
        st.info("No conversations found for this user.")
        st.session_state.pop("user_id", None)
        st.session_state.pop("conversation_id", None)
        return

    useful_conversations = {
        conversation.name: conversation.chat_id for conversation in conversations if conversation.num_messages
    }
    if not useful_conversations:
        st.info("No conversations found for this user.")
        st.session_state.pop("user_id", None)
        st.session_state.pop("conversation_id", None)
        return

    # Navigation
    menu_options = {"(Select a Conversation)": None} | useful_conversations
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
        host=get_env("GRINNING_CAT_API_HOST").replace("https://", "").replace("http://", ""),
        port=int(get_env("GRINNING_CAT_API_PORT")),
        auth_key=st.session_state.get("token"),
        secure_connection=get_env_bool("GRINNING_CAT_API_SECURE_CONNECTION"),
    )


def render_json_form(data: Dict, types: Dict, prefix: str = "", special_keys: List[str] | None = None) -> Dict:
    """Recursively render form fields for JSON data."""
    def infer_type() -> str:
        if value is None:
            return types.get(key)
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "string"
        if isinstance(value, (list, dict)):
            return "json"
        return "string"

    def create_input_field() -> Any:
        field_type = infer_type()
        if field_type == "boolean":
            return st.checkbox(key, value=value, key=path)
        if field_type == "integer":
            return st.number_input(key, value=value, step=1, key=path)
        if field_type == "float":
            return st.number_input(key, value=value, step=0.1, format="%.2f", key=path)
        if field_type == "string":
            return st.text_input(key, value=value, key=path)
        if field_type == "json":
            # For nested structures, show as editable JSON text
            json_str = json.dumps(value, indent=2)
            r = st.text_area(key, value=json_str, height=100, key=path)
            try:
                return json.loads(r)
            except:
                st.error(f"Invalid JSON in field '{key}'")
                return value
        return value

    special_keys = special_keys or []
    result = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key

        if (
                isinstance(value, dict)
                and not any(isinstance(v, (list, dict)) for v in value.values())
                and key not in special_keys
        ):
            # Simple dict - render fields inline
            st.subheader(key)
            result[key] = render_json_form(value, path, special_keys=special_keys)
        else:
            # Render a single field
            result[key] = create_input_field()

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


def cache_cookie_me():
    client = GrinningCatClient(build_client_configuration())
    res = client.auth.me(st.session_state.get("token"))
    me_data = res.model_dump()

    # Store in session state for immediate access
    st.session_state["me"] = me_data

    # Also update cookie for persistence across sessions
    set_cookie(
        "me",
        json.dumps(me_data),
        duration_days=int(get_env("GRINNING_CAT_JWT_EXPIRE_MINUTES")) / (60 * 24),
    )
