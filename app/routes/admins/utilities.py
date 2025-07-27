import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.constants import CLIENT_CONFIGURATION


def factory_reset():
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Factory Reset")

    st.warning("""
    ⚠️ **Danger Zone** ⚠️  
    This will completely reset the entire application to its initial state.  
    All settings, memories, and plugins will be deleted.  
    This action cannot be undone!
    """)

    if st.button("Perform Factory Reset", type="primary"):
        try:
            with st.spinner("Performing factory reset..."):
                result = client.admins.post_factory_reset()

            if result.deleted_settings and result.deleted_plugin_folders and result.deleted_memories:
                st.toast("Factory reset completed successfully!", icon="✅")
            else:
                st.toast("Factory reset partially failed", icon="❌")
            st.json({
                "Settings deleted": result.deleted_settings,
                "Plugin folders deleted": result.deleted_plugin_folders,
                "Memories deleted": result.deleted_memories
            })
        except Exception as e:
            st.toast(f"Error performing factory reset: {e}", icon="❌")


def list_agents():
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Agent Management")

    try:
        agents = client.admins.get_agents()

        if not agents:
            st.info("No agents found")
            return

        st.write("### Existing Agents")
        for agent in agents:
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Agent ID**: `{agent}`")

            with col2:
                if st.button("Reset", key=f"reset_{agent}", type="primary", help="Reset agent settings and memories"):
                    st.session_state["agent_to_reset"] = agent

            with col3:
                if st.button("Destroy", key=f"destroy_{agent}", type="primary", help="Permanently destroy agent and all associated data"):
                    st.session_state["agent_to_destroy"] = agent

            st.divider()

        # Reset confirmation
        if "agent_to_reset" in st.session_state:
            agent = st.session_state["agent_to_reset"]
            st.warning(f"⚠️ Are you sure you want to permanently reset agent `{agent}`?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Destroy Agent", type="primary"):
                    try:
                        with st.spinner(f"Resetting agent {agent}..."):
                            result = client.admins.post_agent_reset(agent_id=agent)
                        if result.deleted_settings:
                            st.toast(f"Agent {agent} reset successfully!", icon="✅")
                            st.session_state.pop("agent_to_reset", None)
                            time.sleep(1)  # Wait for a moment before rerunning
                            st.rerun()
                        else:
                            st.toast(f"Failed to reset agent {agent}", icon="❌")
                    except Exception as e:
                        st.toast(f"Error resetting agent: {e}", icon="❌")

            with col2:
                if st.button("Cancel"):
                    st.session_state.pop("agent_to_reset", None)
                    st.rerun()

        # Destroy confirmation
        if "agent_to_destroy" in st.session_state:
            agent = st.session_state["agent_to_destroy"]
            st.warning(f"⚠️ Are you sure you want to permanently destroy agent `{agent}`?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Destroy Agent", type="primary"):
                    try:
                        with st.spinner(f"Destroying agent {agent}..."):
                            result = client.admins.post_agent_destroy(agent_id=agent)
                        if result.deleted_settings and result.deleted_memories:
                            st.toast(f"Agent {agent} destroyed successfully!", icon="✅")
                            st.session_state.pop("agent_to_destroy", None)
                            time.sleep(1)  # Wait for a moment before rerunning
                            st.rerun()
                        else:
                            st.toast(f"Failed to completely destroy agent {agent}", icon="❌")
                    except Exception as e:
                        st.toast(f"Error destroying agent: {e}", icon="❌")
            with col2:
                if st.button("Cancel"):
                    st.session_state.pop("agent_to_destroy", None)
                    st.rerun()

    except Exception as e:
        st.error(f"Error fetching agents: {e}")


def create_agent():
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Create New Agent")

    with st.form("create_agent_form", clear_on_submit=True):
        agent_id = st.text_input("Agent ID", help="Unique identifier for the new agent")

        submitted = st.form_submit_button("Create Agent")
        if submitted:
            if not agent_id:
                st.error("Agent ID is required")
            else:
                try:
                    with st.spinner(f"Creating agent {agent_id}..."):
                        result = client.admins.post_agent_create(agent_id=agent_id)
                    if result.created:
                        st.toast(f"Agent {agent_id} created successfully!", icon="✅")
                    else:
                        st.toast(f"Failed to create agent {agent_id}", icon="❌")
                except Exception as e:
                    st.toast(f"Error creating agent: {e}", icon="❌")


def admin_system_management(container):
    st.title("System Management Dashboard")

    # Navigation
    menu_options = {
        "(Select a menu)": None,
        "Agent Management": "agent_management",
        "Create Agent": "create_agent",
        "Factory Reset": "factory_reset"
    }
    choice = st.selectbox("Menu", menu_options)

    if menu_options[choice] == "agent_management":
        list_agents()
    elif menu_options[choice] == "create_agent":
        create_agent()
    elif menu_options[choice] == "factory_reset":
        factory_reset()
