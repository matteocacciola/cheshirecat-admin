import json
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.constants import CLIENT_CONFIGURATION
from app.utils import get_factory_settings, build_agents_select, run_toast


def list_auth_handlers(agent_id: str):
    run_toast()

    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Authentication Handlers")

    try:
        settings = client.auth_handler.get_auth_handlers_settings(agent_id)

        st.write("### Available Authentication Handlers")
        if settings.settings:
            for handler in settings.settings:
                col1, col2, col3 = st.columns([0.8, 0.05, 0.15])
                is_selected = handler.name == settings.selected_configuration
                with col1:
                    with st.expander(handler.name):
                        st.json(get_factory_settings(handler, is_selected))

                with col2:
                    if is_selected:
                        st.write('<div class="picked">✅</div>', unsafe_allow_html=True)

                with col3:
                    if st.button("Edit" if is_selected else "Select", key=f"edit_{handler.name}"):
                        edit_auth_handler(agent_id, handler.name, is_selected)
        else:
            st.info("No authentication handler found")
    except Exception as e:
        st.error(f"Error fetching authentication handlers: {e}")


@st.dialog(title="Edit Authentication Handler", width="large")
def edit_auth_handler(agent_id: str, handler_name: str, is_selected: bool):
    client = CheshireCatClient(CLIENT_CONFIGURATION)

    try:
        handler_settings = client.auth_handler.get_auth_handler_settings(handler_name, agent_id)

        with st.form("edit_auth_handler_form", clear_on_submit=True):
            st.write(f"Editing: **{handler_name}**")

            # Display current settings as editable JSON
            edited_settings = st.text_area(
                "Settings (JSON format)",
                value=json.dumps(get_factory_settings(handler_settings, is_selected), indent=4),
                height=300
            )

            st.write("**Note:** Make sure to keep the JSON format valid. You can use online JSON validators if needed.")
            st.divider()

            submitted = st.form_submit_button("Save Changes")
            if submitted:
                try:
                    settings_dict = json.loads(edited_settings)

                    client.auth_handler.put_auth_handler_settings(
                        auth_handler=handler_name,
                        agent_id=agent_id,
                        values=settings_dict
                    )
                    st.session_state["toast"] = {
                        "message": f"Handler {handler_name} updated successfully!", "icon": "✅"
                    }
                except json.JSONDecodeError:
                    st.session_state["toast"] = {"message": "Invalid JSON format", "icon": "❌"}
                except Exception as e:
                    st.session_state["toast"] = {"message": f"Error updating handler: {e}", "icon": "❌"}

                st.rerun()
    except Exception as e:
        st.error(f"Error fetching handler settings: {e}")
        if st.button("Back to list"):
            st.rerun()


def auth_handlers_management(container):
    st.title("Authentication Handlers Management Dashboard")

    with container:
        build_agents_select()

    if "agent_id" in st.session_state:
        list_auth_handlers(st.session_state.agent_id)
