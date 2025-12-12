import os
import tempfile
import json
import time

import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.utils import (
    get_factory_settings,
    build_agents_select,
    run_toast,
    show_overlay_spinner,
    build_client_configuration,
    render_json_form,
)

# Pagination settings
ITEMS_PER_PAGE = 10


def render_pagination_controls(section_key, current_page, total_pages):
    """Render pagination controls for a section."""
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if st.button("← Previous", key=f"{section_key}_prev", disabled=current_page == 0):
            st.session_state[f"{section_key}_page"] -= 1
            st.rerun()

    with col2:
        st.markdown(
            f"<div style='text-align: center; margin-top: 0.5em;'>Page {current_page + 1} of {total_pages}</div>",
            unsafe_allow_html=True
        )

    with col3:
        page_input = st.number_input(
            "Go to page",
            min_value=1,
            max_value=total_pages,
            value=current_page + 1,
            step=1,
            key=f"{section_key}_page_input",
            label_visibility="collapsed"
        )
        if page_input != current_page + 1:
            st.session_state[f"{section_key}_page"] = page_input - 1
            st.rerun()

    with col4:
        if st.button("Next →", key=f"{section_key}_next", disabled=current_page >= total_pages - 1):
            st.session_state[f"{section_key}_page"] += 1
            st.rerun()


def paginate_items(items, section_key, items_per_page):
    """Paginate a list of items and return the current page items."""
    # Initialize session state for pagination
    if f"{section_key}_page" not in st.session_state:
        st.session_state[f"{section_key}_page"] = 0

    total_items = len(items)
    total_pages = (total_items - 1) // items_per_page + 1 if total_items > 0 else 1
    current_page = st.session_state[f"{section_key}_page"]

    # Calculate pagination range
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    paginated_items = items[start_idx:end_idx]

    return paginated_items, current_page, total_pages


def render_installed_plugin(p, core_plugins_ids, client):
    """Render a single installed plugin row."""
    col0, col1, col2, col3, col4 = st.columns([0.05, 0.63, 0.1, 0.12, 0.1])

    with col0:
        if p.thumb:
            st.markdown(
                f'<img src="{p.thumb}" alt="" style="width: 100%; margin-bottom: 1em;" />',
                unsafe_allow_html=True
            )
            # st.image(p.thumb, width="stretch")

    with col1:
        with st.expander(f"Plugin: {p.name} (ID: {p.id})", icon="🔌"):
            st.json(p.model_dump())

    with col2:
        if st.button("View Details", key=f"view_{p.id}"):
            view_plugin_details(p.id)

    with col3:
        if p.id in core_plugins_ids:
            if p.id != "base_plugin" and st.button(
                    f"{'Untoggle' if p.local_info['active'] else 'Toggle'} Plugin",
                    key=f"toggle_{p.id}",
                    help=f"{'Untoggle' if p.local_info['active'] else 'Toggle'} this plugin. This is a core plugin and cannot be uninstalled.",
            ):
                spinner_container = show_overlay_spinner("Toggling plugin...")
                try:
                    client.admins.put_toggle_plugin(p.id)
                    st.toast(f"Plugin {p.id} toggled successfully!", icon="✅")
                    time.sleep(1)
                except Exception as e:
                    st.error(f"Error toggling plugin: {e}", icon="❌")
                finally:
                    spinner_container.empty()
                st.rerun()
        else:
            if st.button(
                    "Uninstall Plugin",
                    key=f"uninstall_{p.id}",
                    help="Uninstall this plugin",
            ):
                st.session_state["plugin_to_uninstall"] = p.id

    with col4:
        if p.id != "base_plugin" and p.local_info["active"] and st.button("Manage", key=f"manage_{p.id}"):
            manage_plugin(p.id)


def render_registry_plugin(registry_plugin, client):
    """Render a single registry plugin row."""
    plugin_url = registry_plugin.id

    col0, col1, col2 = st.columns([0.05, 0.65, 0.3])

    with col0:
        if registry_plugin.thumb:
            st.markdown(
                f'<img src="{registry_plugin.thumb}" alt="" style="width: 100%; margin-bottom: 1em;" />',
                unsafe_allow_html=True
            )
            # st.image(registry_plugin.thumb, width="stretch")

    with col1:
        with st.expander(f"Plugin: {registry_plugin.name} (Version: {registry_plugin.version})", icon="🔌"):
            st.write(f"**Version**: {registry_plugin.version}")
            st.write(f"**Author**: {registry_plugin.author_name} - [Profile]({registry_plugin.author_url})")
            st.write(f"**Description**: {registry_plugin.description or 'No description provided'}")
            st.write(f"**Plugin URL**: [Link]({plugin_url})")
            st.write(f"**Tags**: {registry_plugin.tags or 'No tags'}")

    with col2:
        if st.button("Install Plugin", key=f"install_{registry_plugin.name}"):
            spinner_container = show_overlay_spinner("Installing plugin...")
            try:
                client.admins.post_install_plugin_from_registry(url=plugin_url)
                st.toast("Installation successful!", icon="✅")
            except Exception as e:
                st.toast(f"Error installing plugin: {e}", icon="❌")
            finally:
                spinner_container.empty()
            st.rerun()


def render_uninstall_confirmation(client):
    """Render the uninstall confirmation dialog."""
    if not (plugin := st.session_state.get("plugin_to_uninstall")):
        return

    st.warning(f"⚠️ Are you sure you want to permanently uninstall plugin `{plugin}`?")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Yes, Uninstall Plugin", type="primary"):
            spinner_container = show_overlay_spinner("Uninstalling plugin...")
            try:
                client.admins.delete_plugin(plugin)
                st.toast(f"Plugin {plugin} uninstalled successfully!", icon="✅")
                st.session_state.pop("plugin_to_uninstall", None)
            except Exception as e:
                st.error(f"Error uninstalling plugin: {e}", icon="❌")
            finally:
                spinner_container.empty()
            st.rerun()

    with col2:
        if st.button("Cancel"):
            st.session_state.pop("plugin_to_uninstall", None)
            st.rerun()


def list_plugins():
    run_toast()

    client = CheshireCatClient(build_client_configuration())
    st.header("Available Plugins")

    # Search functionality
    search_query = st.text_input("Search plugins", "")

    try:
        core_plugins_ids = client.custom.get_custom("/admins/core_plugins", "system")
        plugins = client.admins.get_available_plugins(plugin_name=search_query)

        if not plugins:
            st.info("No plugins found matching your search")
            return

        # ==================== INSTALLED PLUGINS ====================
        st.subheader("Installed plugins")
        st.markdown(f"Plugins (found {len(plugins.installed)} plugins):")

        if plugins.installed:
            paginated_installed, current_page, total_pages = paginate_items(
                plugins.installed, "installed", ITEMS_PER_PAGE
            )

            # Display paginated installed plugins
            for p in paginated_installed:
                render_installed_plugin(p, core_plugins_ids, client)

            # Pagination controls for installed plugins
            if total_pages > 1:
                render_pagination_controls("installed", current_page, total_pages)

        # Uninstall confirmation
        render_uninstall_confirmation(client)

        st.divider()

        # ==================== REGISTRY PLUGINS ====================
        st.subheader("Registry plugins")
        st.write(f"Found {len(plugins.registry)} plugins:")

        if plugins.registry:
            sorted_registry = sorted(plugins.registry, key=lambda x: x.name)
            paginated_registry, current_page, total_pages = paginate_items(
                sorted_registry, "registry", ITEMS_PER_PAGE
            )

            # Display paginated registry plugins
            for registry_plugin in paginated_registry:
                render_registry_plugin(registry_plugin, client)

            # Pagination controls for registry plugins
            if total_pages > 1:
                render_pagination_controls("registry", current_page, total_pages)

    except Exception as e:
        st.error(f"Error fetching plugins: {e}")


@st.dialog(title="Plugin Details", width="large")
def view_plugin_details(plugin_id: str):
    client = CheshireCatClient(build_client_configuration())
    try:
        plugin_details = client.admins.get_plugin_details(plugin_id).data

        # Basic info
        st.subheader("Basic Information")
        col1, col2 = st.columns(2)
        col1.write(f"**Name**: {plugin_details['name']}")
        col1.write(f"**Version**: {plugin_details['version']}")
        col1.write(f"**Author**: {plugin_details.get('author', 'Unknown')}")
        col2.write(f"**Active**: {'✅' if plugin_details.get('local_info', {}).get('active') else '❌'}")
        col2.write(f"**Plugin ID**: {plugin_id}")

        # Description
        st.write(f"**Description**: {plugin_details.get('description', 'No description provided')}")

        # Hooks
        if hooks := plugin_details.get("local_info", {}).get("hooks"):
            st.subheader("Hooks")
            for hook in hooks:
                st.write(f"- {hook['name']} (priority: {hook['priority']})")

        # Tools
        if tools := plugin_details.get("local_info", {}).get("tools"):
            st.subheader("Tools")
            for tool in tools:
                st.write(f"- {tool['name']}")

        # Forms
        if forms := plugin_details.get("local_info", {}).get("forms"):
            st.subheader("Forms")
            for form in forms:
                st.write(f"- {form['name']}")

        # MCP clients
        if mcp_clients := plugin_details.get("local_info", {}).get("mcp_clients"):
            st.subheader("MCP Clients")
            for client_info in mcp_clients:
                st.write(f"- {client_info['name']}")

        # Endpoints
        if endpoints := plugin_details.get("local_info", {}).get("endpoints"):
            st.subheader("API Endpoints")
            for endpoint in endpoints:
                st.write(f"- {endpoint['name']} (tags: {', '.join(endpoint['tags'])})")
    except Exception as e:
        st.error(f"Error fetching plugin details: {e}")
        if st.button("Back to list"):
            st.rerun()


@st.dialog(title="Manage Plugin", width="large")
def manage_plugin(plugin_id: str):
    build_agents_select("plugins")
    if not (agent_id := st.session_state.get("agent_id")):
        return

    client = CheshireCatClient(build_client_configuration())

    # fetch the plugin
    try:
        r = client.plugins.get_available_plugins(agent_id, plugin_id)
        plugins_active = [r for r in r.installed if r.local_info and r.local_info.get("active")]
        is_plugin_active = any(plugin.id == plugin_id for plugin in plugins_active)
    except Exception as e:
        st.error(f"Error fetching plugin: {e}")
        return

    # if the plugin is installed, fetch its settings and display them in a form to be edited
    st.header(f"Manage Plugin: {plugin_id}")
    if is_plugin_active:
        try:
            if plugin_settings := get_factory_settings(
                    client.plugins.get_plugin_settings(plugin_id, agent_id),
                    is_selected=True
            ):
                st.subheader("Plugin Settings")
                with st.form("plugin_settings_form", clear_on_submit=True, enter_to_submit=False):
                    # Render the form
                    edited_settings = render_json_form(plugin_settings)

                    if st.form_submit_button("Save Changes"):
                        spinner_container = show_overlay_spinner("Saving plugin settings...")
                        try:
                            client.plugins.put_plugin_settings(plugin_id, agent_id, edited_settings)
                            st.session_state["toast"] = {
                                "message": f"Plugin {plugin_id} settings updated successfully!", "icon": "✅"
                            }
                        except json.JSONDecodeError:
                            st.session_state["toast"] = {"message": "Invalid JSON format", "icon": "❌"}
                        except Exception as e:
                            st.session_state["toast"] = {"message": f"Error updating plugin settings: {e}", "icon": "❌"}
                        finally:
                            spinner_container.empty()
                        st.rerun()
        except Exception as e:
            st.error(f"Error fetching plugin settings: {e}")
    else:
        st.warning("""This plugin is not currently active for the selected agent.
You have to activate the plugin before managing its settings.""")

        try:
            plugin_settings = client.admins.get_plugin_settings(plugin_id)
            with st.expander("Plugin's default configuration", icon="⚙️"):
                st.json(get_factory_settings(plugin_settings, is_selected=True))
        except Exception as e:
            st.error(f"Error fetching plugin settings: {e}")

    st.divider()

    col1, col2, col3 = st.columns(3)
    # in any case, display a button to toggle / untoggle the plugin
    with col1:
        if st.button(f"{'Untoggle' if is_plugin_active else 'Toggle'} Plugin"):
            spinner_container = show_overlay_spinner(f"{'Untoggling' if is_plugin_active else 'Toggling'} plugin...")
            try:
                client.plugins.put_toggle_plugin(plugin_id, agent_id)
                st.session_state["toast"] = {
                    "message": f"Plugin {plugin_id} {'untoggled' if is_plugin_active else 'toggled'} successfully!",
                    "icon": "✅",
                }
            except Exception as e:
                st.session_state["toast"] = {
                    "message": f"Error {'untoggling' if is_plugin_active else 'toggling'} plugin: {e}",
                    "icon": "❌"
                }
            finally:
                spinner_container.empty()
            st.rerun()

    with col2:
        if is_plugin_active and st.button("Reset Plugin"):
            spinner_container = show_overlay_spinner("Resetting the plugin to the factory status...")
            try:
                client.plugins.post_plugin_reset_settings(plugin_id, agent_id)
                st.session_state["toast"] = {
                    "message": f"Plugin {plugin_id} reset successfully!",
                    "icon": "✅",
                }
            except Exception as e:
                st.session_state["toast"] = {
                    "message": f"Error resetting plugin: {e}",
                    "icon": "❌"
                }
            finally:
                spinner_container.empty()
            st.rerun()

    with col3:
        if st.button("Back to list"):
            st.rerun()


def install_plugin_from_file():
    client = CheshireCatClient(build_client_configuration())
    st.header("Install Plugin from File")

    with st.form("upload_plugin_form", clear_on_submit=True, enter_to_submit=False):
        uploaded_file = st.file_uploader(
            "Choose a plugin ZIP file",
            type=["zip"],
            accept_multiple_files=False
        )

        submitted = st.form_submit_button("Install Plugin")
        if submitted and uploaded_file is not None:
            spinner_container = show_overlay_spinner("Installing plugin from file...")

            # Create a temporary directory
            with tempfile.TemporaryDirectory() as tmp_dir:
                try:
                    # Create the temporary file path with the original filename
                    tmp_file_path = os.path.join(tmp_dir, uploaded_file.name)

                    # Write the uploaded content to the temporary file
                    with open(tmp_file_path, "wb") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())

                    # Pass the temporary file path to the SDK method
                    result = client.admins.post_install_plugin_from_zip(path_zip=tmp_file_path)
                    st.toast(f"Plugin {uploaded_file.name} is being installed!", icon="✅")
                    st.json(result.model_dump())
                except Exception as e:
                    st.toast(f"Error installing plugin: {e}", icon="❌")
                finally:
                    spinner_container.empty()
        elif submitted:
            st.toast("Please select a file to upload", icon="⚠️")


def view_plugin_settings():
    client = CheshireCatClient(build_client_configuration())
    st.header("All Plugin Settings")

    try:
        plugins_settings = client.admins.get_plugins_settings()
        for plugin_settings in plugins_settings.settings:
            with st.expander(f"Plugin: {plugin_settings.name} (ID: {plugin_settings.id})", icon="⚙️"):
                st.json(get_factory_settings(plugin_settings, is_selected=False))
    except Exception as e:
        st.error(f"Error fetching plugin settings: {e}")


def admin_plugins_management():
    st.title("Plugins Management Dashboard")

    # Navigation
    menu_options = {
        "(Select a menu)": None,
        "Browse Plugins": "browse_plugins",
        "Install from File": "install_from_file",
    }
    choice = st.selectbox("Menu", menu_options)

    if menu_options[choice] == "browse_plugins":
        list_plugins()
        return
    if menu_options[choice] == "install_from_file":
        install_plugin_from_file()