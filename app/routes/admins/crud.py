import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.utils import run_toast, show_overlay_spinner, build_client_configuration


def create_admin():
    client = CheshireCatClient(build_client_configuration())

    # Initialize form key in session state if not present
    if "admin_form_key" not in st.session_state:
        st.session_state.admin_form_key = 0

    st.header("Create New Admin")
    with st.form(f"create_admin_form_{st.session_state.admin_form_key}", enter_to_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        # Permissions editor
        st.subheader("Permissions")

        available_permissions = client.admins.get_available_permissions()
        selected_permissions = {}
        for res, perms in available_permissions.items():
            st.write(f"**{res}**")
            cols = st.columns(len(perms))
            permissions = []
            for i, perm in enumerate(perms):
                is_checked = cols[i].checkbox(perm, key=f"{res}_{perm}_{st.session_state.admin_form_key}")
                if is_checked:
                    permissions.append(perm)
            selected_permissions[res] = permissions

        if not st.form_submit_button("Create Admin"):
            return

        if not username or not password:
            st.error("Username and password are required")
            return

        if all(len(perms) == 0 for perms in selected_permissions.values()):
            st.error("At least one permission must be selected")
            return

        spinner_container = show_overlay_spinner("Creating admin...")
        try:
            result = client.admins.post_admin(username, password, selected_permissions)
            st.toast(f"Admin {result.username} created successfully!", icon="✅")
            time.sleep(1)

            # Increment form key to reset the form on next rerun
            st.session_state.admin_form_key += 1
            st.rerun()
        except Exception as e:
            st.toast(f"Error creating admin: {e}", icon="❌")
        finally:
            spinner_container.empty()


def list_admins(skip: int = 0, limit: int = 100):
    run_toast()

    client = CheshireCatClient(build_client_configuration())
    st.header("List All Admins")

    try:
        admins = client.admins.get_admins(limit=limit, skip=skip)
        if admins:
            st.write(f"Found {len(admins)} admins:")
            for admin in admins:
                col1, col2, col3, col4 = st.columns([0.7, 0.1, 0.1, 0.1])

                with col1:
                    with st.expander(f"Admin: {admin.username} (ID: {admin.id})", icon="👤"):
                        st.json(admin.model_dump())

                with col2:
                    # Action buttons
                    if st.button("View", key=f"view_{admin.id}"):
                        get_admin(admin.id)

                with col3:
                    if st.button("Update", key=f"update_{admin.id}"):
                        update_admin(admin.id)

                with col4:
                    if (
                            admin.username != "admin"
                            and st.button("Delete", key=f"delete_{admin.id}", help="Permanently delete this item")
                    ):
                        st.session_state["admin_to_delete"] = admin

            # Delete confirmation
            if admin := st.session_state.get("admin_to_delete"):
                st.warning(f"⚠️ Are you sure you want to permanently delete admin `{admin.id}`?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Delete Admin", type="primary"):
                        try:
                            spinner_container = show_overlay_spinner(f"Deleting admin {admin.id}...")
                            client.admins.delete_admin(admin.id)
                            st.toast(f"Admin {admin.id} deleted successfully!", icon="✅")
                            st.session_state.pop("admin_to_delete", None)
                            time.sleep(1)  # Wait for a moment before rerunning
                        except Exception as e:
                            st.error(f"Error deleting admin: {e}", icon="❌")
                        finally:
                            spinner_container.empty()
                        st.rerun()
                with col2:
                    if st.button("Cancel"):
                        st.session_state.pop("admin_to_delete", None)
                        st.rerun()
            return

        st.info("No admin found")
    except Exception as e:
        st.error(f"Error fetching admins: {e}")


@st.dialog(title="Admin Details", width="large")
def get_admin(admin_id: str):
    client = CheshireCatClient(build_client_configuration())
    st.header(f"Admin Details for ID: {admin_id}")

    try:
        admin_data = client.admins.get_admin(admin_id)
        st.json(admin_data.model_dump())
    except Exception as e:
        st.error(f"Error fetching admin `{admin_id}`: {e}")


@st.dialog(title="Update Details", width="large")
def update_admin(admin_id: str):
    client = CheshireCatClient(build_client_configuration())
    st.header(f"Update Admin ID: {admin_id}")

    try:
        admin_data = client.admins.get_admin(admin_id)
    except Exception:
        st.error(f"Admin with ID `{admin_id}` not found")
        return

    with st.form("update_admin_form", enter_to_submit=False):
        new_username = st.text_input("Username", value=admin_data.username)
        new_password = st.text_input("Password (leave blank to keep current)", type="password")

        # Permissions editor
        st.subheader("Permissions")
        current_permissions = admin_data.permissions
        available_permissions = client.admins.get_available_permissions()

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

        if not st.form_submit_button("Update Admin"):
            return

        if not new_username:
            st.error("Username cannot be empty")
            return

        if all(len(perms) == 0 for perms in selected_permissions.values()):
            st.error("At least one permission must be selected")
            return

        try:
            spinner_container = show_overlay_spinner(f"Updating admin {admin_id}...")

            result = client.admins.put_admin(
                admin_id,
                username=new_username,
                password=new_password or None,
                permissions=selected_permissions
            )
            st.session_state["toast"] = {"message": f"Admin {result.username} updated successfully!", "icon": "✅"}
        except Exception as e:
            st.session_state["toast"] = {"message": f"Error updating admin `{admin_id}`: {e}", "icon": "❌"}
        finally:
            spinner_container.empty()
            time.sleep(1)
            st.rerun()


# Streamlit UI
def admin_management():
    st.title("Admin Management Dashboard")
    
    # Navigation
    menu_options = {"(Select a menu)": None, "List Admins": "list_admins", "Create Admin": "create_admin"}
    choice = st.selectbox("Menu", menu_options)

    if menu_options[choice] == "list_admins":
        list_admins()
        return

    if menu_options[choice] == "create_admin":
        create_admin()
