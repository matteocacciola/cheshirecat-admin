import json
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.utils import (
    get_factory_settings,
    run_toast,
    show_overlay_spinner,
    build_client_configuration,
    render_json_form,
)


def list_embedders():
    run_toast()

    client = CheshireCatClient(build_client_configuration())
    st.header("Embedders")

    try:
        settings = client.embedder.get_embedders_settings()

        st.write("### Available Embedders")
        if not settings.settings:
            st.info("No embedder found")
            return

        for embedder in settings.settings:
            col1, col2, col3 = st.columns([0.8, 0.05, 0.15])
            is_selected = embedder.name == settings.selected_configuration
            with col1:
                with st.expander(embedder.name):
                    st.json(get_factory_settings(embedder, is_selected))

            with col2:
                if is_selected:
                    st.write('<div class="picked">✅</div>', unsafe_allow_html=True)

            with col3:
                if st.button("Edit" if is_selected else "Select", key=f"edit_{embedder.name}"):
                    edit_embedder(embedder.name, is_selected)
    except Exception as e:
        st.error(f"Error fetching embedders: {e}")


@st.dialog(title="Edit Embedder", width="large")
def edit_embedder(embedder_name: str, is_selected: bool):
    client = CheshireCatClient(build_client_configuration())

    st.subheader(f"Editing: **{embedder_name}**")
    try:
        embedder_settings = get_factory_settings(
                client.embedder.get_embedder_settings(embedder_name),
                is_selected=is_selected
        )
        with st.form("edit_embedder_form", clear_on_submit=True, enter_to_submit=False):
            # Render the form
            edited_settings = render_json_form(embedder_settings)
            if st.form_submit_button("Save Changes"):
                try:
                    spinner_container = show_overlay_spinner("Saving settings...")
                    client.embedder.put_embedder_settings(
                        embedder=embedder_name,
                        values=edited_settings,
                    )
                    st.session_state["toast"] = {
                        "message": f"Embedder {embedder_name} updated successfully!", "icon": "✅"
                    }
                except json.JSONDecodeError:
                    st.session_state["toast"] = {"message": "Invalid JSON format", "icon": "❌"}
                except Exception as e:
                    st.session_state["toast"] = {"message": f"Error updating embedder: {e}", "icon": "❌"}
                finally:
                    spinner_container.empty()

                st.rerun()
    except Exception as e:
        st.error(f"Error fetching embedder settings: {e}")

    st.divider()
    if st.button("Back to list"):
        st.rerun()


def embedders_management():
    st.title("Embedders Management Dashboard")

    list_embedders()
