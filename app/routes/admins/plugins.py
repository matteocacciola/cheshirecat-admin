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
)


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

        st.subheader("Installed plugins")
        st.markdown(f"Plugins (found {len(plugins.installed)} plugins):")

        # for each installed plugin, create an expander, a button to view details, a button to uninstall and a button
        # to manage settings
        for p in plugins.installed:
            col1, col2, col3, col4 = st.columns([0.7, 0.1, 0.1, 0.1])

            with col1:
                with st.expander(f"Plugin: {p.name} (ID: {p.id})", icon="🔌"):
                    st.json(p.model_dump())

            with col2:
                if st.button("View Details", key=f"view_{p.id}"):
                    view_plugin_details(p.id, should_uninstall=False)

            with col3:
                if p.id in core_plugins_ids:
                    if p.id != "base_plugin" and st.button(
                        f"{'Untoggle' if p.active else 'Toggle'} Plugin",
                        key=f"toggle_{p.id}",
                        type="primary",
                        help=f"{'Untoggle' if p.active else 'Toggle'} this plugin. This is a core plugin and cannot be uninstalled.",
                    ):
                        spinner_container = show_overlay_spinner("Toggling plugin...")
                        try:
                            client.admins.put_toggle_plugin(p.id)
                            st.toast(f"Plugin {p.id} toggled successfully!", icon="✅")
                            time.sleep(1)  # wait a bit to let the backend process the toggle
                        except Exception as e:
                            st.error(f"Error toggling plugin: {e}", icon="❌")
                        finally:
                            spinner_container.empty()
                        st.rerun()
                else:
                    if st.button(
                        "Uninstall Plugin",
                        key=f"uninstall_{p.id}",
                        type="primary",
                        help="Uninstall this plugin",
                    ):
                        st.session_state["plugin_to_uninstall"] = p.id

            with col4:
                if st.button("Manage", key=f"manage_{p.id}"):
                    manage_plugin(p.id)

        # Uninstall confirmation
        if "plugin_to_uninstall" in st.session_state:
            plugin = st.session_state["plugin_to_uninstall"]
            st.warning(f"⚠️ Are you sure you want to permanently uninstall plugin `{plugin}`?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Uninstall Plugin", type="primary"):
                    spinner_container = show_overlay_spinner("Uninstalling plugin...")
                    try:
                        client.plugins.delete_plugin(plugin)
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

        st.divider()

        st.subheader("Registry plugins")
        st.write(f"Found {len(plugins.registry)} plugins:")
        for registry_plugin in sorted(plugins.registry, key=lambda x: x.name):
            col1, col2 = st.columns([0.7, 0.3])

            with col1:
                with st.expander(f"Plugin: {registry_plugin.name} (Version: {registry_plugin.version})", icon="🔌"):
                    st.write(f"**Version**: {registry_plugin.version}")
                    st.write(f"**Author**: {registry_plugin.author_name} - [Profile]({registry_plugin.author_url})")
                    st.write(f"**Description**: {registry_plugin.description or 'No description provided'}")
                    st.write(f"**Plugin URL**: [Link]({registry_plugin.plugin_url})")
                    st.write(f"**Tags**: {registry_plugin.tags or 'No tags'}")

            with col2:
                if st.button("Install Plugin", key=f"install_{registry_plugin.name}"):
                    spinner_container = show_overlay_spinner("Installing plugin...")
                    plugin_url = registry_plugin.plugin_url
                    try:
                        client.admins.post_install_plugin_from_registry(url=plugin_url)
                        st.toast("Installation successful!", icon="✅")
                    except Exception as e:
                        st.toast(f"Error installing plugin: {e}", icon="❌")
                    finally:
                        spinner_container.empty()
                    st.rerun()

    except Exception as e:
        st.error(f"Error fetching plugins: {e}")


@st.dialog(title="Plugin Details", width="large")
def view_plugin_details(plugin_id: str, should_uninstall: bool):
    client = CheshireCatClient(build_client_configuration())
    try:
        plugin_details = client.admins.get_plugin_details(plugin_id).data

        # Basic info
        st.subheader("Basic Information")
        col1, col2 = st.columns(2)
        col1.write(f"**Name**: {plugin_details['name']}")
        col1.write(f"**Version**: {plugin_details['version']}")
        col1.write(f"**Author**: {plugin_details.get('author', 'Unknown')}")
        col2.write(f"**Active**: {'✅' if plugin_details['active'] else '❌'}")
        col2.write(f"**Plugin ID**: {plugin_id}")

        # Description
        st.write(f"**Description**: {plugin_details.get('description', 'No description provided')}")

        # Hooks
        if plugin_details.get("hooks"):
            st.subheader("Hooks")
            for hook in plugin_details["hooks"]:
                st.write(f"- {hook['name']} (priority: {hook['priority']})")

        # Tools
        if plugin_details.get("tools"):
            st.subheader("Tools")
            for tool in plugin_details["tools"]:
                st.write(f"- {tool['name']}")

        # Forms
        if plugin_details.get("forms"):
            st.subheader("Forms")
            for form in plugin_details["forms"]:
                st.write(f"- {form['name']}")

        # Endpoints
        if plugin_details.get("endpoints"):
            st.subheader("API Endpoints")
            for endpoint in plugin_details["endpoints"]:
                st.write(f"- {endpoint['name']} (tags: {', '.join(endpoint['tags'])})")

        # Actions
        st.divider()
        col1, col2 = st.columns(2)

        if not should_uninstall:
            return

        with col1:
            if st.button("Uninstall Plugin", type="primary"):
                spinner_container = show_overlay_spinner("Uninstalling plugin...")
                try:
                    result = client.plugins.delete_plugin(plugin_id)
                    st.session_state["toast"] = {
                        "message": f"Plugin {result.deleted} uninstalled successfully!", "icon": "✅"
                    }
                except Exception as e:
                    st.session_state["toast"] = {"message": f"Error uninstalling plugin: {e}", "icon": "❌"}
                finally:
                    spinner_container.empty()
                st.rerun()

        with col2:
            if st.button("Back to list"):
                st.rerun()
    except Exception as e:
        st.error(f"Error fetching plugin details: {e}")
        if st.button("Back to list"):
            st.rerun()


@st.dialog(title="Manage Plugin", width="large")
def manage_plugin(plugin_id: str):
    build_agents_select()
    if "agent_id" not in st.session_state:
        return

    agent_id = st.session_state.agent_id
    client = CheshireCatClient(build_client_configuration())

    # fetch the plugin
    try:
        plugins_installed = client.plugins.get_available_plugins(agent_id, plugin_id).installed
        is_plugin_installed = any(plugin.id == plugin_id for plugin in plugins_installed)
    except Exception as e:
        st.error(f"Error fetching plugin: {e}")
        return

    # if the plugin is installed, fetch its settings and display them in a form to be edited
    st.header(f"Manage Plugin: {plugin_id}")
    if is_plugin_installed:
        try:
            plugin_settings = client.plugins.get_plugin_settings(plugin_id, agent_id)

            st.subheader("Plugin Settings")
            with st.form("plugin_settings_form", clear_on_submit=True):
                # Display current settings as editable JSON
                edited_settings = st.text_area(
                    "Settings (JSON format)",
                    value=json.dumps(get_factory_settings(plugin_settings, is_selected=True), indent=4),
                    height=300
                )

                st.write(
                    "**Note:** Make sure to keep the JSON format valid. You can use online JSON validators if needed."
                )
                st.divider()

                submitted = st.form_submit_button("Save Changes")
                if submitted:
                    spinner_container = show_overlay_spinner("Saving plugin settings...")
                    try:
                        settings_dict = json.loads(edited_settings)
                        client.plugins.put_plugin_settings(plugin_id, agent_id, settings_dict)
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

    col1, col2 = st.columns(2)
    # in any case, display a button to toggle / untoggle the plugin
    with col1:
        if st.button(f"{'Untoggle' if is_plugin_installed else 'Toggle'} Plugin", type="primary"):
            spinner_container = show_overlay_spinner(f"{'Untoggling' if is_plugin_installed else 'Toggling'} plugin...")
            try:
                client.plugins.put_toggle_plugin(plugin_id, agent_id)
                st.session_state["toast"] = {
                    "message": f"Plugin {plugin_id} {'untoggled' if is_plugin_installed else 'toggled'} successfully!",
                    "icon": "✅",
                }
            except Exception as e:
                st.session_state["toast"] = {
                    "message": f"Error {'untoggling' if is_plugin_installed else 'toggling'} plugin: {e}",
                    "icon": "❌"
                }
            finally:
                spinner_container.empty()
            st.rerun()

    with col2:
        if st.button("Back to list"):
            st.rerun()


def install_plugin_from_file():
    client = CheshireCatClient(build_client_configuration())
    st.header("Install Plugin from File")

    with st.form("upload_plugin_form", clear_on_submit=True):
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