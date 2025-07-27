import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.constants import CLIENT_CONFIGURATION
from app.utils import run_toast, show_overlay_spinner


def create_admin():
    client = CheshireCatClient(CLIENT_CONFIGURATION)

    st.header("Create New Admin")
    with st.form("create_admin_form", clear_on_submit=True):
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
                is_checked = cols[i].checkbox(perm, key=f"{res}_{perm}")
                if is_checked:
                    permissions.append(perm)
            selected_permissions[res] = permissions

        if st.form_submit_button("Create Admin"):
            if not username or not password:
                st.error("Username and password are required")
            elif not selected_permissions:
                st.error("At least one permission must be selected")
            else:
                spinner_container = show_overlay_spinner("Creating admin...")
                try:
                    result = client.admins.post_admin(username, password, selected_permissions)
                    st.toast(f"Admin {result.username} created successfully!", icon="✅")
                    st.json(result)
                except Exception as e:
                    st.toast(f"Error creating admin: {e}", icon="❌")
                finally:
                    spinner_container.empty()


def list_admins(skip: int = 0, limit: int = 100):
    run_toast()

    client = CheshireCatClient(CLIENT_CONFIGURATION)
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
                            and st.button("Delete", key=f"delete_{admin.id}", type="primary", help="Permanently delete this item")
                    ):
                        st.session_state["admin_to_delete"] = admin

            # Delete confirmation
            if "admin_to_delete" in st.session_state:
                admin = st.session_state["admin_to_delete"]
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
        else:
            st.info("No admin found")
    except Exception as e:
        st.error(f"Error fetching admins: {e}")


@st.dialog(title="Admin Details", width="large")
def get_admin(admin_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header(f"Admin Details for ID: {admin_id}")

    try:
        admin_data = client.admins.get_admin(admin_id)
        st.json(admin_data.model_dump())
    except Exception as e:
        st.error(f"Error fetching admin `{admin_id}`: {e}")


@st.dialog(title="Update Details", width="large")
def update_admin(admin_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header(f"Update Admin ID: {admin_id}")

    try:
        admin_data = client.admins.get_admin(admin_id)
    except Exception:
        st.error(f"Admin with ID `{admin_id}` not found")
        return

    with st.form("update_admin_form", clear_on_submit=True):
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

        if st.form_submit_button("Update Admin"):
            if not new_username:
                st.error("Username cannot be empty")
            elif not selected_permissions:
                st.error("At least one permission must be selected")
            try:
                spinner_container = show_overlay_spinner(f"Updating admin {admin_id}...")

                result = client.admins.put_admin(
                    admin_id,
                    username=new_username,
                    password=new_password or None,
                    permissions=selected_permissions
                )
                st.session_state["toast"] = {"message": f"Admin {result.username} updated successfully!", "icon": "✅"}
                st.json(result)
            except Exception as e:
                st.session_state["toast"] = {"message": f"Error updating admin `{admin_id}`: {e}", "icon": "❌"}
            finally:
                spinner_container.empty()

            st.rerun()


# Streamlit UI
def admin_management(container):
    st.title("Admin Management Dashboard")
    
    # Navigation
    menu_options = {"(Select a menu)": None, "List Admins": "list_admins", "Create Admin": "create_admin"}
    choice = st.selectbox("Menu", menu_options)

    if menu_options[choice] == "list_admins":
        list_admins()

    elif menu_options[choice] == "create_admin":
        create_admin()
