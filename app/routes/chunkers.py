import json
import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.constants import CLIENT_CONFIGURATION
from app.utils import get_factory_settings, build_agents_select


def list_chunkers(agent_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Chunkers")

    try:
        settings = client.chunker.get_chunkers_settings(agent_id)

        st.write("### Available Chunkers")
        if settings.settings:
            for chunker in settings.settings:
                col1, col2, col3 = st.columns([0.8, 0.05, 0.15])
                is_selected = chunker.name == settings.selected_configuration
                with col1:
                    with st.expander(chunker.name):
                        st.json(get_factory_settings(chunker, is_selected))

                with col2:
                    if is_selected:
                        st.write('<div class="picked">✅</div>', unsafe_allow_html=True)

                with col3:
                    if st.button("Edit" if is_selected else "Select", key=f"edit_{chunker.name}"):
                        edit_chunker(agent_id, chunker.name, is_selected)
        else:
            st.info("No chunker found")
    except Exception as e:
        st.error(f"Error fetching chunkers: {e}")


@st.dialog(title="Edit Chunker", width="large")
def edit_chunker(agent_id: str, chunker_name: str, is_selected: bool):
    client = CheshireCatClient(CLIENT_CONFIGURATION)

    try:
        chunker_settings = client.chunker.get_chunker_settings(chunker_name, agent_id)

        with st.form("edit_chunker_form", clear_on_submit=True):
            st.write(f"Editing: **{chunker_name}**")

            # Display current settings as editable JSON
            edited_settings = st.text_area(
                "Settings (JSON format)",
                value=json.dumps(get_factory_settings(chunker_settings, is_selected), indent=4),
                height=300
            )

            st.write("**Note:** Make sure to keep the JSON format valid. You can use online JSON validators if needed.")
            st.divider()

            submitted = st.form_submit_button("Save Changes")
            if submitted:
                try:
                    settings_dict = json.loads(edited_settings)

                    client.chunker.put_chunker_settings(
                        chunker=chunker_name,
                        agent_id=agent_id,
                        values=settings_dict
                    )
                    st.toast(f"Chunker {chunker_name} updated successfully!", icon="✅")
                except json.JSONDecodeError:
                    st.toast("Invalid JSON format", icon="❌")
                except Exception as e:
                    st.toast(f"Error updating chunker: {e}", icon="❌")

                time.sleep(3)  # Wait for a moment before rerunning
                st.rerun()
    except Exception as e:
        st.error(f"Error fetching chunker settings: {e}")
        if st.button("Back to list"):
            st.rerun()


def chunkers_management(container):
    st.title("Chunkers Management Dashboard")

    with container:
        build_agents_select()
    if "agent_id" in st.session_state:
        list_chunkers(st.session_state.agent_id)
