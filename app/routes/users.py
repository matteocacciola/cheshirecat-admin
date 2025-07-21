import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.constants import CLIENT_CONFIGURATION
from app.utils import build_agents_select


def create_user(agent_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)

    st.header("Create New User")
    with st.form("create_user_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        # Permissions editor
        st.subheader("Permissions")

        available_permissions = client.users.get_available_permissions()
        selected_permissions = {}
        for res, perms in available_permissions.items():
            st.write(f"**{res}**")
            cols = st.columns(len(perms))
            permissions = []
            for i, perm in enumerate(perms):
                is_checked = cols[i].checkbox(perm, key=f"{res}_{perm}")
                if is_checked:
                    permissions.append(perm)
            selected_permissions[res] = permissions

        submitted = st.form_submit_button("Create User")
        if submitted:
            if not username or not password:
                st.error("Username and password are required")
            else:
                try:
                    result = client.users.post_user(agent_id, username, password, permissions if permissions else None)
                    st.toast(f"Admin {result.username} created successfully!", icon="✅")
                    st.json(result)
                except Exception as e:
                    st.toast(f"Error creating admin: {e}", icon="❌")


def list_users(agent_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("List All Users")

    try:
        users = client.users.get_users(agent_id)
        if users:
            st.write(f"Found {len(users)} users:")
            for user in users:
                col1, col2, col3, col4 = st.columns([0.7, 0.1, 0.1, 0.1])

                with col1:
                    with st.expander(f"User: {user.username} (ID: {user.id})", icon="👤"):
                        st.json(user.model_dump())

                with col2:
                    # Action buttons
                    if st.button("View", key=f"view_{user.id}"):
                        get_user(agent_id, user.id)

                with col3:
                    if st.button("Update", key=f"update_{user.id}"):
                        update_user(agent_id, user.id)

                with col4:
                    if (
                            user.username != "user"
                            and st.button("Delete", key=f"delete_{user.id}", type="primary", help="Permanently delete this item")
                    ):
                        st.session_state["user_to_delete"] = user

            # Delete confirmation
            if "user_to_delete" in st.session_state:
                user = st.session_state["user_to_delete"]
                st.warning(f"⚠️ Are you sure you want to permanently delete user `{user.id}`?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Delete User", type="primary"):
                        try:
                            with st.spinner(f"Deleting admin {user.id}..."):
                                client.users.delete_user(agent_id, user.id)
                                st.toast(f"Admin {user.id} deleted successfully!", icon="✅")
                                st.session_state.pop("user_to_delete", None)
                                time.sleep(3)  # Wait for a moment before rerunning
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting user: {e}", icon="❌")
                with col2:
                    if st.button("Cancel"):
                        st.session_state.pop("user_to_delete", None)
                        st.rerun()
        else:
            st.info("No user found")
    except Exception as e:
        st.error(f"Error fetching users: {e}")


@st.dialog(title="User Details", width="large")
def get_user(agent_id: str, user_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header(f"User Details for ID: {user_id}")

    try:
        user_data = client.users.get_user(user_id, agent_id)
        st.json(user_data.model_dump())
    except Exception as e:
        st.error(f"Error fetching user `{user_id}`: {e}")


@st.dialog(title="Update Details", width="large")
def update_user(agent_id: str, user_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header(f"Update User ID: {user_id}")

    try:
        user_data = client.users.get_user(user_id, agent_id)
    except Exception:
        st.error(f"User with ID `{user_id}` not found")
        return

    with st.form("update_user_form"):
        new_username = st.text_input("Username", value=user_data.username)
        new_password = st.text_input("Password (leave blank to keep current)", type="password")

        # Permissions editor
        st.subheader("Permissions")
        current_permissions = user_data.permissions
        available_permissions = client.users.get_available_permissions()

        selected_permissions = {}
        for res, perms in available_permissions.items():
            st.write(f"**{res}**")
            cols = st.columns(len(perms))
            permissions = []
            for i, perm in enumerate(perms):
                is_checked = cols[i].checkbox(perm, value=perm in current_permissions.get(res, []), key=f"{res}_{perm}")
                if is_checked:
                    permissions.append(perm)
            selected_permissions[res] = permissions

        st.divider()

        submitted = st.form_submit_button("Update User")
        if submitted:
            try:
                result = client.users.put_user(
                    agent_id=agent_id,
                    user_id=user_id,
                    username=new_username,
                    password=new_password or None,
                    permissions=selected_permissions or None,
                )
                st.toast(f"User {result.username} updated successfully!", icon="✅")
                st.json(result)
            except Exception as e:
                st.toast(f"Error updating user `{user_id}`: {e}", icon="❌")


# Streamlit UI
def users_management(container):
    st.title("User Management Dashboard")

    with container:
        build_agents_select()
    if "agent_id" in st.session_state:
        agent_id = st.session_state.agent_id

        # Sidebar navigation
        menu_options = ["List Users", "Create User"]
        choice = st.selectbox("Menu", menu_options)

        if choice == "List Users":
            list_users(agent_id)

        elif choice == "Create User":
            create_user(agent_id)
