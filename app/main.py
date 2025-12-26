import time
import streamlit as st
from dotenv import load_dotenv
from cheshirecat_python_sdk import CheshireCatClient
from streamlit_js_eval import get_cookie

from app.constants import CHECK_INTERVAL
from app.env import get_env
from app.utils import build_client_configuration, clear_auth_cookies


def apply_custom_css():
    """Apply custom CSS for enhanced styling"""
    hide_dev_toolbar = """
    /* Hide the ENTIRE development toolbar */
    .stDeployButton {display: none;}
    
    /* If the above doesn't work, try these selectors */
    #stDeployButton {display: none;}
    button[kind="header"] {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    div[data-testid="stDecoration"] {display: none;}
    div[data-testid="stStatusWidget"] {display: none;}
    
    /* Hide the hamburger menu too */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    """

    st.markdown(f"""
    <style>
    {hide_dev_toolbar if get_env('CHESHIRE_CAT_ENVIRONMENT') == 'prod' else ''}
    
    /* Main content area */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}

    /* Custom card styling */
    .info-card {{
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }}

    /* Navigation title styling */
    .nav-title {{
        font-size: 1.5rem;
        font-weight: bold;
        // color: #2c3e50;
        margin-bottom: 1rem;
        padding: 0.5rem;
        border-bottom: 2px solid #667eea;
    }}

    /* Status indicators */
    .status-indicator {{
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }}

    .status-online {{ background-color: #2ecc71; }}
    .status-offline {{ background-color: #e74c3c; }}
    .status-warning {{ background-color: #f39c12; }}
    
    .picked {{ margin-top: 0.65rem; margin-left: 0.5rem; margin-right: auto; }}
    </style>
    """, unsafe_allow_html=True)


@st.fragment(run_every=CHECK_INTERVAL)  # Run every 5 seconds
def check_and_display_status():
    """Check backend status and display it"""
    current_status = st.session_state.get("status_connection", "Warning")
    try:
        client = CheshireCatClient(build_client_configuration())
        client.health_check.liveness()
        status_connection = "Online"
    except Exception as e:
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

    # Add a flag to track if we've attempted cookie check
    st.session_state["token"] = st.session_state.get("token", get_env("CHESHIRE_CAT_API_KEY"))

    if "initial_auth_check_done" not in st.session_state:
        st.session_state["initial_auth_check_done"] = st.session_state["token"] is not None

    # First time: check for cookie without blocking UI
    if not st.session_state["initial_auth_check_done"]:
        # Mark that we've started the check
        st.session_state["initial_auth_check_done"] = True

        # Try to get cookie (async - returns None initially)
        cookie_token = get_cookie("token")

        if cookie_token:
            # If we get a token immediately (rare), use it
            st.session_state["token"] = cookie_token
        else:
            # Most common case: cookie check is async
            # Show loading state instead of login page
            st.sidebar.info("🔍 Checking authentication...")
            # Return a special page key to show loading in main area too
            return "loading"

    # Normal flow continues after initial check
    if not st.session_state.get("token"):
        cookie_token = get_cookie("token")  # Try again after async result

        if cookie_token:
            st.session_state["token"] = cookie_token
            time.sleep(1)
            st.rerun()  # Safe rerun now that we have token
        else:
            time.sleep(1)
            st.sidebar.warning("Please log in to access the admin features.")
            return "login"

    # Navigation menu with icons
    navigation_options = {
        "menu_chat": {
            "💬 Chat": "chat",
            "🗂️ Memory & Chats": "memory",
            "📚 Knowledge Base": "rag",
        },
        "menu_users": {
            "👥 Users": "users",
        },
        "menu_management": {
            "🔌 Plugins": "plugins",
            "🧬 AI Models": "ai_models",
            "🔐 Authentication Handlers": "auth_handlers",
            "🔪 Chunkers": "chunkers",
            "🧠 Embedders": "embedders",
            "📁 File Handlers": "file_handlers",
            "🔗 Vector Databases": "vector_databases",
        },
        "menu_system": {
            "⚙️ System": "system",
        }
    }

    # Create the navigation menu
    for menu_key, menu_items in navigation_options.items():
        for item_name, item_key in menu_items.items():
            if "selected_page" not in st.session_state:
                st.session_state["selected_page"] = None
            if st.sidebar.button(
                item_name,
                key=f"nav_{item_key}",
                type="secondary",
                use_container_width=True,
                disabled=(
                        st.session_state.get("status_connection", None) != "Online"
                        or st.session_state["selected_page"] == item_key
                ),
            ):
                st.session_state["selected_page"] = item_key
                st.rerun()  # Force immediate rerun

        # Add separator
        st.sidebar.divider()

    # System status section
    status_connection = st.session_state.get("status_connection", "Warning")
    st.sidebar.markdown(f"""
    ### 📡 System Status: <span class="status-indicator status-{status_connection.lower()}"></span> {status_connection}
    """, unsafe_allow_html=True)

    # Add separator
    st.sidebar.divider()

    if st.session_state.get("token") == get_env("CHESHIRE_CAT_API_KEY"):
        st.sidebar.info("""You are logged in with the default API key.
For security reasons, please consider creating admin users and logging in by credentials.""")
        return st.session_state["selected_page"]

    # logout button
    if st.sidebar.button("Logout", type="primary", use_container_width=True):
        st.session_state["token"] = None
        st.session_state["status_connection"] = "Warning"

        clear_auth_cookies()
        time.sleep(1)  # Wait for cookie to clear

        st.toast("Logged out successfully.", icon="🚪")

        time.sleep(1)  # Wait for a moment before rerunning
        st.rerun()
    return st.session_state["selected_page"]


def main():
    """Main application function"""
    # Apply custom styling
    apply_custom_css()

    check_and_display_status()

    # Render sidebar navigation and get selected page
    current_page = render_sidebar_navigation()

    if st.session_state.get("status_connection", None) != "Online":
        st.error("Cheshire Cat backend is offline. Please check your connection.")
        return

    # Handle loading state
    if current_page == "loading":
        st.title("Loading...")
        st.info("Checking your authentication status. This will only take a moment.")
        # Optionally add a spinner
        with st.spinner("Checking for saved login..."):
            time.sleep(0.5)  # Brief pause
        return

    if current_page == "login":
        from app.routes.login import login_page

        login_page()
        return

    if current_page == "chat":
        from app.routes.message import chat

        if "messages" in st.session_state:
            st.session_state.pop("messages", None)

        chat()
        return

    if current_page == "ai_models":
        from app.routes.llms import llms_management

        llms_management()
        return

    if current_page == "auth_handlers":
        from app.routes.auth_handlers import auth_handlers_management

        auth_handlers_management()
        return

    if current_page == "chunkers":
        from app.routes.chunkers import chunkers_management

        chunkers_management()
        return

    if current_page == "embedders":
        from app.routes.embedders import embedders_management

        embedders_management()
        return

    if current_page == "file_handlers":
        from app.routes.file_managers import file_managers_management

        file_managers_management()
        return

    if current_page == "rag":
        from app.routes.rabbit_hole import rabbit_hole_management

        rabbit_hole_management()
        return

    if current_page == "plugins":
        from app.routes.admins.plugins import admin_plugins_management

        admin_plugins_management()
        return

    if current_page == "users":
        from app.routes.users import users_management

        users_management()
        return

    if current_page == "vector_databases":
        from app.routes.vector_databases import vector_databases_management

        vector_databases_management()
        return

    if current_page == "memory":
        from app.routes.memories import memory_management

        memory_management()
        return

    if current_page == "system":
        from app.routes.utilities import utilities_management

        utilities_management()
        return

    # show a welcome message if no page is selected
    st.title("Welcome to the Cheshire Cat Admin UI 🐱")
    st.markdown("""
    Use the sidebar to navigate through different sections of the admin interface.
    
    Ensure that you are logged in to access all features.
    """)


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
