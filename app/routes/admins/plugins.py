import time
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient

from app.constants import CLIENT_CONFIGURATION
from app.utils import get_factory_settings


def list_plugins():
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Available Plugins")

    # Search functionality
    search_query = st.text_input("Search plugins", "")

    try:
        plugins = client.admins.get_available_plugins(plugin_name=search_query)
        if not plugins:
            st.info("No plugins found matching your search")
            return


        st.subheader("Installed plugins")
        st.write(f"Found {len(plugins.installed)} plugins:")
        # for each installed plugins, create an expander, a button to view details, and a button to uninstall
        for installed_plugin in plugins.installed:
            # Action buttons
            col1, col2, col3 = st.columns([0.7, 0.15, 0.15])

            with col1:
                with st.expander(f"Plugin: {installed_plugin.name} (ID: {installed_plugin.id})", icon="🔌"):
                    st.json(installed_plugin.model_dump())

                with col2:
                    if st.button("View Details", key=f"view_{installed_plugin.id}"):
                        view_plugin_details(installed_plugin.id)

                with col3:
                    if (
                            installed_plugin.id != "core_plugin"
                            and st.button("Uninstall Plugin", key=f"uninstall_{installed_plugin.id}", type="primary", help="Uninstall this plugin")
                    ):
                        st.session_state["plugin_to_uninstall"] = installed_plugin.id

        # Uninstall confirmation
        if "plugin_to_uninstall" in st.session_state:
            plugin = st.session_state["plugin_to_uninstall"]
            st.warning(f"⚠️ Are you sure you want to permanently uninstall plugin `{plugin}`?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Uninstall Plugin", type="primary"):
                    try:
                        with st.spinner(f"Uninstalling plugin {plugin}..."):
                            client.plugins.delete_plugin(plugin)
                            st.toast(f"Plugin {plugin} uninstalled successfully!", icon="✅")
                            st.session_state.pop("plugin_to_uninstall", None)
                            time.sleep(3)  # Wait for a moment before rerunning
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error uninstalling plugin: {e}", icon="❌")
            with col2:
                if st.button("Cancel"):
                    st.session_state.pop("plugin_to_uninstall", None)
                    st.rerun()

        st.subheader("Registry plugins")
        st.write(f"Found {len(plugins.registry)} plugins:")
        for registry_plugin in sorted(plugins.registry, key=lambda x: x.name):
            col1, col2 = st.columns([0.7, 0.3])

            with col1:
                with st.expander(f"Plugin: {registry_plugin.name} (ID: {registry_plugin.id})", icon="🔌"):
                    st.write(f"**Version**: {registry_plugin.version}")
                    st.write(f"**Author**: {registry_plugin.author_name} - [Profile]({registry_plugin.author_url})")
                    st.write(f"**Description**: {registry_plugin.description or 'No description provided'}")
                    st.write(f"**Plugin URL**: [Link]({registry_plugin.plugin_url})")
                    st.write(f"**Tags**: {registry_plugin.tags or 'No tags'}")

            with col2:
                if st.button("Install Plugin", key=f"install_{registry_plugin.name}"):
                    plugin_url = registry_plugin.plugin_url
                    try:
                        client.admins.post_install_plugin_from_registry(url=plugin_url)
                        st.toast("Installation successful!", icon="✅")
                    except Exception as e:
                        st.toast(f"Error installing plugin: {e}", icon="❌")
    except Exception as e:
        st.error(f"Error fetching plugins: {e}")


@st.dialog(title="Plugin Details", width="large")
def view_plugin_details(plugin_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
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

        with col1:
            if plugin_id != "core_plugin" and st.button("Uninstall Plugin", type="primary"):
                try:
                    result = client.plugins.delete_plugin(plugin_id)
                    st.toast(f"Plugin {result.deleted} uninstalled successfully!", icon="✅")
                except Exception as e:
                    st.toast(f"Error uninstalling plugin: {e}", icon="❌")

        with col2:
            if st.button("Back to list"):
                st.rerun()
    except Exception as e:
        st.error(f"Error fetching plugin details: {e}")
        if st.button("Back to list"):
            st.rerun()


def install_plugin_from_file():
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Install Plugin from File")

    with st.form("upload_plugin_form"):
        uploaded_file = st.file_uploader(
            "Choose a plugin ZIP file",
            type=["zip"],
            accept_multiple_files=False
        )

        submitted = st.form_submit_button("Install Plugin")
        if submitted and uploaded_file is not None:
            try:
                # Note: The SDK would need to handle file uploads
                result = client.admins.post_install_plugin_from_zip(path_zip=uploaded_file.name)
                st.toast(f"Plugin {uploaded_file.name} is being installed!", icon="✅")
                st.json(result.model_dump())
            except Exception as e:
                st.toast(f"Error installing plugin: {e}", icon="❌")
        elif submitted:
            st.toast("Please select a file to upload", icon="⚠️")


def view_plugin_settings():
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("All Plugin Settings")

    try:
        plugins_settings = client.admins.get_plugins_settings()
        for plugin_settings in plugins_settings.settings:
            with st.expander(f"Plugin: {plugin_settings.name} (ID: {plugin_settings.id})", icon="⚙️"):
                st.json(get_factory_settings(plugin_settings, is_selected=False))
    except Exception as e:
        st.error(f"Error fetching plugin settings: {e}")


def admin_plugins_management(container):
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
    elif menu_options[choice] == "install_from_file":
        install_plugin_from_file()
