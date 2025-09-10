import json
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.utils import (
    get_factory_settings,
    build_agents_select,
    run_toast,
    show_overlay_spinner,
    build_client_configuration,
)


def list_vector_databases(agent_id: str):
    run_toast()

    client = CheshireCatClient(build_client_configuration())
    st.header("Vector Databases")

    try:
        settings = client.vector_database.get_vector_databases_settings(agent_id)

        st.write("### Available Vector Databases")
        if not settings.settings:
            st.info("No vector database found")
            return

        for vector_database in settings.settings:
            col1, col2, col3 = st.columns([0.8, 0.05, 0.15])
            is_selected = vector_database.name == settings.selected_configuration
            with col1:
                with st.expander(vector_database.name):
                    st.json(get_factory_settings(vector_database, is_selected))

            with col2:
                if is_selected:
                    st.write('<div class="picked">✅</div>', unsafe_allow_html=True)

            with col3:
                if st.button("Edit" if is_selected else "Select", key=f"edit_{vector_database.name}"):
                    edit_vector_database(agent_id, vector_database.name, is_selected)
    except Exception as e:
        st.error(f"Error fetching vector databases: {e}")


@st.dialog(title="Edit Vector Database", width="large")
def edit_vector_database(agent_id: str, vector_database_name: str, is_selected: bool):
    client = CheshireCatClient(build_client_configuration())

    try:
        vector_db_settings = client.vector_database.get_vector_database_settings(vector_database_name, agent_id)

        with st.form("edit_vector_database_form", clear_on_submit=True):
            st.write(f"Editing: **{vector_database_name}**")

            # Display current settings as editable JSON
            edited_settings = st.text_area(
                "Settings (JSON format)",
                value=json.dumps(get_factory_settings(vector_db_settings, is_selected), indent=4),
                height=300
            )

            st.write("**Note:** Make sure to keep the JSON format valid. You can use online JSON validators if needed.")
            st.divider()

            if not st.form_submit_button("Save Changes"):
                return

            try:
                spinner_container = show_overlay_spinner("Saving settings...")
                settings_dict = json.loads(edited_settings)

                client.vector_database.put_vector_database_settings(
                    vector_database=vector_database_name,
                    agent_id=agent_id,
                    values=settings_dict
                )
                st.session_state["toast"] = {
                    "message": f"Vector database {vector_database_name} updated successfully!", "icon": "✅"
                }
            except json.JSONDecodeError:
                st.session_state["toast"] = {"message": "Invalid JSON format", "icon": "❌"}
            except Exception as e:
                st.session_state["toast"] = {"message": f"Error updating vector database: {e}", "icon": "❌"}
            finally:
                spinner_container.empty()

            st.rerun()
    except Exception as e:
        st.error(f"Error fetching vector database settings: {e}")
        if st.button("Back to list"):
            st.rerun()


def vector_databases_management():
    st.title("Vector Databases Management Dashboard")

    build_agents_select()
    if "agent_id" in st.session_state:
        list_vector_databases(st.session_state.agent_id)
