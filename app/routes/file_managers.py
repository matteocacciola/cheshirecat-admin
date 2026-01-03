import json
from typing import Dict
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.utils import (
    get_factory_settings,
    build_agents_select,
    run_toast,
    show_overlay_spinner,
    build_client_configuration,
    render_json_form,
    has_access,
)


def _list_file_managers(agent_id: str, cookie_me: Dict | None):
    run_toast()

    if not has_access("FILE_MANAGER", "READ", cookie_me):
        st.error("You do not have access to view file managers for this agent.")
        return

    client = CheshireCatClient(build_client_configuration())
    st.header("File Managers")

    try:
        settings = client.file_manager.get_file_managers_settings(agent_id)

        st.write("### Available File Managers")
        if not settings.settings:
            st.info("No file manager found")
            return

        for file_manager in settings.settings:
            col1, col2, col3 = st.columns([0.8, 0.05, 0.15])
            is_selected = file_manager.name == settings.selected_configuration
            with col1:
                with st.expander(file_manager.name):
                    st.json(get_factory_settings(file_manager, is_selected))

            with col2:
                if is_selected:
                    st.write('<div class="picked">✅</div>', unsafe_allow_html=True)

            with col3:
                if has_access("FILE_MANAGER", "WRITE", cookie_me):
                    if st.button("Edit" if is_selected else "Select", key=f"edit_{file_manager.name}"):
                        _edit_file_manager(agent_id, file_manager.name, is_selected)
                else:
                    st.button(
                        "Edit",
                        key=f"edit_{file_manager.name}",
                        disabled=True,
                        help="You do not have permission to edit file managers.",
                    )
    except Exception as e:
        st.error(f"Error fetching file managers: {e}")


@st.dialog(title="Edit File Manager", width="large")
def _edit_file_manager(agent_id: str, file_manager_name: str, is_selected: bool, cookie_me: Dict | None):
    if not has_access("FILE_MANAGER", "WRITE", cookie_me):
        st.error("You do not have access to edit file managers for this agent.")
        return

    client = CheshireCatClient(build_client_configuration())

    st.subheader(f"Editing: **{file_manager_name}**")
    try:
        file_manager_settings = get_factory_settings(
            client.file_manager.get_file_manager_settings(file_manager_name, agent_id),
            is_selected=is_selected
        )
        if file_manager_settings:
            with st.form("edit_file_manager_form", clear_on_submit=True, enter_to_submit=False):
                # Render the form
                edited_settings = render_json_form(file_manager_settings)
                if st.form_submit_button("Save Changes"):
                    try:
                        spinner_container = show_overlay_spinner("Saving settings...")
                        client.file_manager.put_file_manager_settings(
                            file_manager=file_manager_name,
                            agent_id=agent_id,
                            values=edited_settings,
                        )
                        st.session_state["toast"] = {
                            "message": f"File manager {file_manager_name} updated successfully!", "icon": "✅"
                        }
                    except json.JSONDecodeError:
                        st.session_state["toast"] = {"message": "Invalid JSON format", "icon": "❌"}
                    except Exception as e:
                        st.session_state["toast"] = {"message": f"Error updating file manager: {e}", "icon": "❌"}
                    finally:
                        spinner_container.empty()

                    st.rerun()
    except Exception as e:
        st.error(f"Error fetching file manager settings: {e}")

    st.divider()
    if st.button("Back to list"):
        st.rerun()


def file_managers_management(cookie_me: Dict | None):
    st.title("File Managers Management Dashboard")

    st.info("""**Disclaimer**: If you want to store the files of the Knowledge Base in a specific file manager,
    please select it in the **File Managers** section and enable the `CCAT_RABBIT_HOLE_STORAGE_ENABLED` environment variable in the CheshireCat.""")

    build_agents_select("file_managers", cookie_me)
    if "agent_id" in st.session_state:
        _list_file_managers(st.session_state["agent_id"], cookie_me)
