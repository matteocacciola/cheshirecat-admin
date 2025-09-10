import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.utils import build_agents_select, build_users_select, show_overlay_spinner, build_client_configuration


def memory_collections(agent_id: str):
    client = CheshireCatClient(build_client_configuration())
    st.header("Memory Collections")

    try:
        collections = client.memory.get_memory_collections(agent_id)

        if not collections.collections:
            st.info("No memory collections found for this agent")
            return

        st.write("### Available Memory Collections")
        for collection in collections.collections:
            col1, col2 = st.columns([0.8, 0.2])

            with col1:
                st.write(f"**{collection.name}**")
                st.write(f"Vectors count: {collection.vectors_count}")

            with col2:
                if st.button("Delete", key=f"destroy_{collection.name}", type="primary", help="Permanently destroy this collection"):
                    st.session_state["collection_to_delete"] = collection.name

            st.divider()

        # Destroy confirmation
        if "collection_to_delete" in st.session_state:
            collection = st.session_state["collection_to_delete"]
            st.warning(f"⚠️ Are you sure you want to permanently destroy collection `{collection}`?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Destroy Collection", type="primary"):
                    try:
                        spinner_container = show_overlay_spinner(f"Destroying collection {collection}...")

                        result = client.memory.delete_all_single_memory_collection_points(collection, agent_id)
                        if result.deleted[collection]:
                            st.toast(f"Collection {collection} destroyed successfully!", icon="✅")
                            st.session_state.pop("collection_to_delete", None)
                            time.sleep(1)  # Wait for a moment before rerunning
                        else:
                            st.toast(f"Failed to completely destroy collection {collection}", icon="❌")
                    except Exception as e:
                        st.toast(f"Error destroying collection: {e}", icon="❌")
                    finally:
                        spinner_container.empty()

                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.pop("collection_to_delete", None)
                    st.rerun()
    except Exception as e:
        st.error(f"Error fetching memory collections: {e}")


def view_conversation_history(agent_id: str, user_id: str):
    client = CheshireCatClient(build_client_configuration())
    st.header("Conversation History")

    try:
        history = client.memory.get_conversation_history(agent_id, user_id)

        if not history.history:
            st.info("No conversation history found for this user")
            return

        st.write("### Conversation History")
        for item in history.history:
            col1, col2 = st.columns([0.8, 0.2])

            with col1:
                st.write(f"**{item.who}**: {item.content.text}")
                if item.content.image:
                    st.image(item.image, caption="Image", use_column_width=True)
                st.divider()

            with col2:
                if st.button("Delete", key=f"delete_{agent_id}_{user_id}"):
                    st.session_state["history_to_delete"] = {"agent": agent_id, "user": user_id}

        # Delete confirmation
        if "history_to_delete" in st.session_state:
            history_ids = st.session_state["history_to_delete"]
            agent_id = history_ids["agent"]
            user_id = history_ids["user"]
            st.warning(f"⚠️ Are you sure you want to permanently delete this conversation history?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete History", type="primary"):
                    try:
                        spinner_container = show_overlay_spinner(
                            f"Deleting conversation history for Agent {agent_id}, User {user_id}..."
                        )

                        result = client.memory.delete_conversation_history(agent_id, user_id)
                        if result.deleted:
                            st.toast(f"Conversation history deleted successfully!", icon="✅")
                            st.session_state.pop("history_to_delete", None)
                            time.sleep(1)  # Wait for a moment before rerunning
                        else:
                            st.toast(f"Failed to delete conversation history", icon="❌")
                    except Exception as e:
                        st.toast(f"Error deleting conversation history: {e}", icon="❌")
                    finally:
                        spinner_container.empty()

                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.pop("history_to_delete", None)
                    st.rerun()
    except Exception as e:
        st.error(f"Error fetching conversation history: {e}")


# Streamlit UI
def memory_management():
    st.title("Memory Management Dashboard")

    build_agents_select()
    if "agent_id" not in st.session_state:
        return

    agent_id = st.session_state.agent_id

    # Navigation
    menu_options = {
        "(Select a menu)": None,
        "List Collections": "list_collections",
        "View Conversation History": "view_conversation_history",
    }
    choice = st.selectbox("Menu", menu_options)

    if menu_options[choice] == "list_collections":
        memory_collections(agent_id)
        return

    if menu_options[choice] == "view_conversation_history":
        build_users_select(agent_id)
        if "user_id" not in st.session_state:
            return

        user_id = st.session_state.user_id
        view_conversation_history(agent_id, user_id)
