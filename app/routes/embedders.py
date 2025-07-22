import json
import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.constants import CLIENT_CONFIGURATION
from app.utils import get_factory_settings


def list_embedders():
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Embedders")

    try:
        settings = client.embedder.get_embedders_settings()

        st.write("### Available Embedders")
        if settings.settings:
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
        else:
            st.info("No embedder found")
    except Exception as e:
        st.error(f"Error fetching embedders: {e}")


@st.dialog(title="Edit Embedder", width="large")
def edit_embedder(embedder_name: str, is_selected: bool):
    client = CheshireCatClient(CLIENT_CONFIGURATION)

    try:
        embedder_settings = client.embedder.get_embedder_settings(embedder_name)

        with st.form("edit_embedder_form", clear_on_submit=True):
            st.write(f"Editing: **{embedder_name}**")

            # Display current settings as editable JSON
            edited_settings = st.text_area(
                "Settings (JSON format)",
                value=json.dumps(get_factory_settings(embedder_settings, is_selected), indent=4),
                height=300
            )

            st.write("**Note:** Make sure to keep the JSON format valid. You can use online JSON validators if needed.")
            st.divider()

            submitted = st.form_submit_button("Save Changes")
            if submitted:
                try:
                    settings_dict = json.loads(edited_settings)

                    client.embedder.put_embedder_settings(
                        embedder=embedder_name,
                        values=settings_dict
                    )
                    st.toast(f"Embedder {embedder_name} updated successfully!", icon="✅")
                except json.JSONDecodeError:
                    st.toast("Invalid JSON format", icon="❌")
                except Exception as e:
                    st.toast(f"Error updating embedder: {e}", icon="❌")

                time.sleep(3)  # Wait for a moment before rerunning
                st.rerun()
    except Exception as e:
        st.error(f"Error fetching embedder settings: {e}")
        if st.button("Back to list"):
            st.rerun()


def embedders_management(container):
    st.title("Embedders Management Dashboard")

    list_embedders()
