import streamlit as st
from dotenv import load_dotenv

from app.constants import CHECK_INTERVAL


def apply_custom_css():
    """Apply custom CSS for enhanced styling"""
    st.markdown("""
    <style>
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Custom card styling */
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }

    /* Navigation title styling */
    .nav-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
        padding: 0.5rem;
        border-bottom: 2px solid #667eea;
    }

    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-online { background-color: #2ecc71; }
    .status-offline { background-color: #e74c3c; }
    .status-warning { background-color: #f39c12; }
    
    .picked { margin-top: 0.65rem; margin-left: 0.5rem; margin-right: auto; }
    </style>
    """, unsafe_allow_html=True)


@st.fragment(run_every=CHECK_INTERVAL)  # Run every 5 seconds
def check_and_display_status():
    """Check backend status and display it"""
    current_status = st.session_state.get("status_connection", "Warning")

    try:
        from cheshirecat_python_sdk import CheshireCatClient
        from app.constants import CLIENT_CONFIGURATION

        client = CheshireCatClient(CLIENT_CONFIGURATION)
        status_connection = client.http_client.get_client().get("/")
        status_connection = "Online" if status_connection.status_code == 200 else "Offline"
    except Exception:
        status_connection = "Offline"

    st.session_state["status_connection"] = status_connection
    if current_status != status_connection:
        st.rerun()


def render_sidebar_navigation():
    """Render the sidebar navigation menu"""
    # Custom title with styling
    st.sidebar.markdown("""
    <div class="nav-title">
        🐱 Cheshire Cat Admin
    </div>
    """, unsafe_allow_html=True)

    # Navigation menu with icons
    navigation_options = {
        "💬 Chat": "chat",
        "👥 Admins": "admins",
        "🧬 AI Models": "ai_models",
        "🔐 Authentication Handlers": "auth_handlers",
        "🔪 Chunkers": "chunkers",
        "🧠 Embedders": "embedders",
        "📁 File Handlers": "file_handlers",
        "📚 Knowledge Base": "rag",
        "🔌 Plugins": "plugins",
        "👥 Users": "users",
        "🔗 Vector Databases": "vector_databases",
        "🗂️ Vector Memory": "memory",
        "⚙️ System": "system",
    }

    # Create the navigation menu
    selected_page = st.sidebar.radio(
        "Navigation",
        list(navigation_options.keys()),
        label_visibility="collapsed",
        disabled=st.session_state.get("status_connection", None) != "Online",
    )

    # Add separator
    st.sidebar.markdown("---")

    submenu_container = st.sidebar.container()

    # Add separator
    st.sidebar.markdown("---")

    # System status section
    status_connection = st.session_state.get("status_connection", "Warning")
    st.sidebar.markdown(f"""
    ### 📡 System Status: <span class="status-indicator status-{status_connection.lower()}"></span> {status_connection}
    """, unsafe_allow_html=True)

    return navigation_options[selected_page], submenu_container


def main():
    """Main application function"""
    # Apply custom styling
    apply_custom_css()

    check_and_display_status()

    # Render sidebar navigation and get selected page
    current_page, submenu_container = render_sidebar_navigation()

    if st.session_state.get("status_connection", None) != "Online":
        st.error("Cheshire Cat backend is offline. Please check your connection.")
        return

    if current_page == "chat":
        from app.routes.message import chat
        chat(submenu_container)
    elif current_page == "admins":
        from app.routes.admins.crud import admin_management
        admin_management(submenu_container)
    elif current_page == "ai_models":
        from app.routes.llms import llms_management
        llms_management(submenu_container)
    elif current_page == "auth_handlers":
        from app.routes.auth_handlers import auth_handlers_management
        auth_handlers_management(submenu_container)
    elif current_page == "chunkers":
        from app.routes.chunkers import chunkers_management
        chunkers_management(submenu_container)
    elif current_page == "embedders":
        from app.routes.embedders import embedders_management
        embedders_management(submenu_container)
    elif current_page == "file_handlers":
        from app.routes.file_managers import file_managers_management
        file_managers_management(submenu_container)
    elif current_page == "rag":
        from app.routes.rabbit_hole import rabbit_hole_management
        rabbit_hole_management(submenu_container)
    elif current_page == "plugins":
        from app.routes.admins.plugins import admin_plugins_management
        admin_plugins_management(submenu_container)
    elif current_page == "users":
        from app.routes.users import users_management
        users_management(submenu_container)
    elif current_page == "vector_databases":
        from app.routes.vector_databases import vector_databases_management
        vector_databases_management(submenu_container)
    elif current_page == "memory":
        from app.routes.memories import memory_management
        memory_management(submenu_container)
    elif current_page == "system":
        from app.routes.admins.utilities import admin_system_management
        admin_system_management(submenu_container)


# ----- Main application -----
if __name__ == "__main__":
    st.set_page_config(
        page_title="Cheshire Cat Admin UI",
        layout="wide",
        page_icon="🐱",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "mailto:matteo.cacciola@gmail.com",
            "Report a bug": "mailto:matteo.cacciola@gmail.com",
            "About": "Cheshire Cat Admin UI - A Streamlit application for managing the Cheshire Cat backend.",
        }
    )

    load_dotenv()
    main()
