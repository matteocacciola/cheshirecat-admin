import json
import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.constants import CLIENT_CONFIGURATION
from app.utils import get_factory_settings, build_agents_select


def list_file_managers(agent_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("File Managers")

    try:
        settings = client.file_manager.get_file_managers_settings(agent_id)

        st.write("### Available File Managers")
        if settings.settings:
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
                    if st.button("Edit" if is_selected else "Select", key=f"edit_{file_manager.name}"):
                        edit_file_manager(agent_id, file_manager.name, is_selected)
        else:
            st.info("No file manager found")
    except Exception as e:
        st.error(f"Error fetching file managers: {e}")


@st.dialog(title="Edit File Manager", width="large")
def edit_file_manager(agent_id: str, file_manager_name: str, is_selected: bool):
    client = CheshireCatClient(CLIENT_CONFIGURATION)

    try:
        file_manager_settings = client.file_manager.get_file_manager_settings(file_manager_name, agent_id)

        with st.form("edit_file_manager_form"):
            st.write(f"Editing: **{file_manager_name}**")

            # Display current settings as editable JSON
            edited_settings = st.text_area(
                "Settings (JSON format)",
                value=json.dumps(get_factory_settings(file_manager_settings, is_selected), indent=4),
                height=300
            )

            st.write("**Note:** Make sure to keep the JSON format valid. You can use online JSON validators if needed.")
            st.divider()

            submitted = st.form_submit_button("Save Changes")
            if submitted:
                try:
                    settings_dict = json.loads(edited_settings)

                    client.file_manager.put_file_manager_settings(
                        file_manager=file_manager_name,
                        agent_id=agent_id,
                        values=settings_dict
                    )
                    st.toast(f"File manager {file_manager_name} updated successfully!", icon="✅")
                except json.JSONDecodeError:
                    st.toast("Invalid JSON format", icon="❌")
                except Exception as e:
                    st.toast(f"Error updating file manager: {e}", icon="❌")

                time.sleep(3)  # Wait for a moment before rerunning
                st.rerun()
    except Exception as e:
        st.error(f"Error fetching file manager settings: {e}")
        if st.button("Back to list"):
            st.rerun()


def file_managers_management(container):
    st.title("File Managers Management Dashboard")

    with container:
        build_agents_select()
    if "agent_id" in st.session_state:
        list_file_managers(st.session_state.agent_id)
