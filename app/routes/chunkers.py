import json
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.utils import (
    get_factory_settings,
    build_agents_select,
    show_overlay_spinner,
    build_client_configuration,
    render_json_form,
)


def list_chunkers(agent_id: str):
    client = CheshireCatClient(build_client_configuration())
    st.header("Chunkers")

    try:
        settings = client.chunker.get_chunkers_settings(agent_id)

        st.write("### Available Chunkers")
        if not settings.settings:
            st.info("No chunker found")
            return

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
    except Exception as e:
        st.error(f"Error fetching chunkers: {e}")


@st.dialog(title="Edit Chunker", width="large")
def edit_chunker(agent_id: str, chunker_name: str, is_selected: bool):
    client = CheshireCatClient(build_client_configuration())

    st.subheader(f"Editing: **{chunker_name}**")
    try:
        chunker_settings = get_factory_settings(
            client.chunker.get_chunker_settings(chunker_name, agent_id),
            is_selected=is_selected
        )
        with st.form("edit_chunker_form", clear_on_submit=True):
            # Render the form
            edited_settings = render_json_form(chunker_settings)
            if st.form_submit_button("Save Changes"):
                try:
                    spinner_container = show_overlay_spinner("Saving settings...")
                    client.chunker.put_chunker_settings(
                        chunker=chunker_name,
                        agent_id=agent_id,
                        values=edited_settings,
                    )
                    st.session_state["toast"] = {
                        "message": f"Chunker {chunker_name} updated successfully!", "icon": "✅"
                    }
                except json.JSONDecodeError:
                    st.session_state["toast"] = {"message": "Invalid JSON format", "icon": "❌"}
                except Exception as e:
                    st.session_state["toast"] = {"message": f"Error updating chunker: {e}", "icon": "❌"}
                finally:
                    spinner_container.empty()

                st.rerun()
    except Exception as e:
        st.error(f"Error fetching chunker settings: {e}")

    st.divider()
    if st.button("Back to list"):
        st.rerun()


def chunkers_management():
    st.title("Chunkers Management Dashboard")

    build_agents_select()
    if "agent_id" in st.session_state:
        list_chunkers(st.session_state.agent_id)
