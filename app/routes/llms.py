import json
import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.constants import CLIENT_CONFIGURATION
from app.utils import get_factory_settings, build_agents_select


def list_llms(agent_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("LLMs")

    try:
        settings = client.large_language_model.get_large_language_models_settings(agent_id)

        st.write("### Available LLMs")
        if settings.settings:
            for llm in settings.settings:
                col1, col2, col3 = st.columns([0.8, 0.05, 0.15])
                is_selected = llm.name == settings.selected_configuration
                with col1:
                    with st.expander(llm.name):
                        st.json(get_factory_settings(llm, is_selected))

                with col2:
                    if is_selected:
                        st.write('<div class="picked">✅</div>', unsafe_allow_html=True)

                with col3:
                    if st.button("Edit" if is_selected else "Select", key=f"edit_{llm.name}"):
                        edit_llm(agent_id, llm.name, is_selected)
        else:
            st.info("No LLM found")
    except Exception as e:
        st.error(f"Error fetching LLMs: {e}")


@st.dialog(title="Edit LLM", width="large")
def edit_llm(agent_id: str, llm_name: str, is_selected: bool):
    client = CheshireCatClient(CLIENT_CONFIGURATION)

    try:
        llm_settings = client.large_language_model.get_large_language_model_settings(llm_name, agent_id)

        with st.form("edit_llm_form", clear_on_submit=True):
            st.write(f"Editing: **{llm_name}**")

            # Display current settings as editable JSON
            edited_settings = st.text_area(
                "Settings (JSON format)",
                value=json.dumps(get_factory_settings(llm_settings, is_selected), indent=4),
                height=300
            )

            st.write("**Note:** Make sure to keep the JSON format valid. You can use online JSON validators if needed.")
            st.divider()

            submitted = st.form_submit_button("Save Changes")
            if submitted:
                try:
                    settings_dict = json.loads(edited_settings)

                    client.large_language_model.put_large_language_model_settings(
                        llm=llm_name,
                        agent_id=agent_id,
                        values=settings_dict
                    )
                    st.toast(f"LLM {llm_name} updated successfully!", icon="✅")
                except json.JSONDecodeError:
                    st.toast("Invalid JSON format", icon="❌")
                except Exception as e:
                    st.toast(f"Error updating LLM: {e}", icon="❌")

                time.sleep(3)  # Wait for a moment before rerunning
                st.rerun()
    except Exception as e:
        st.error(f"Error fetching LLM settings: {e}")
        if st.button("Back to list"):
            st.rerun()


def llms_management(container):
    st.title("LLMs Management Dashboard")

    with container:
        build_agents_select()
    if "agent_id" in st.session_state:
        list_llms(st.session_state.agent_id)
