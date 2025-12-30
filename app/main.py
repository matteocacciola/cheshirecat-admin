import time
from typing import Dict
import streamlit as st
from dotenv import load_dotenv
from cheshirecat_python_sdk import CheshireCatClient
from streamlit_js_eval import get_cookie

from app.constants import CHECK_INTERVAL
from app.env import get_env
from app.utils import build_client_configuration, clear_auth_cookies, get_cookie_me, build_agents_select, has_access


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
def check_status():
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


def render_sidebar_navigation(cookie_me: Dict | None):
    """Render the sidebar navigation menu"""
    st.session_state["selected_page"] = st.session_state.get("selected_page")

    # Navigation menu with icons
    navigation_options = {
        "menu_chat": {
            "💬 Chat": {
                "page": "chat",
                "allowed": has_access("CHAT", None, cookie_me),
            },
            "🗂️ Memory & Chats": {
                "page": "memory",
                "allowed": has_access("MEMORY", None, cookie_me),
            },
            "📚 Knowledge Base": {
                "page": "rag",
                "allowed": has_access("UPLOAD", None, cookie_me),
            },
        },
        "menu_users": {
            "👥 Users": {
                "page": "users",
                "allowed": has_access("USERS", None, cookie_me),
            },
        },
        "menu_management": {
            "🔌 Plugins": {
                "page": "plugins",
                "allowed": has_access("PLUGIN", None, cookie_me),
            },
            "🧬 AI Models": {
                "page": "ai_models",
                "allowed": has_access("LLM", None, cookie_me),
            },
            "🔐 Authentication Handlers": {
                "page": "auth_handlers",
                "allowed": has_access("AUTH_HANDLER", None, cookie_me),
            },
            "🔪 Chunkers": {
                "page": "chunkers",
                "allowed": has_access("CHUNKER", None, cookie_me),
            },
            "🧠 Embedders": {
                "page": "embedders",
                "allowed": has_access("EMBEDDER", None, cookie_me),
            },
            "📁 File Handlers": {
                "page": "file_handlers",
                "allowed": has_access("FILE_MANAGER", None, cookie_me),
            },
            "🔗 Vector Databases": {
                "page": "vector_databases",
                "allowed": has_access("VECTOR_DATABASE", None, cookie_me),
            }
        },
        "menu_system": {
            "⚙️ System": {
                "page": "system",
                "allowed": has_access("CHESHIRE_CAT", None, cookie_me),
            },
        },
    }

    # Create the navigation menu
    for menu_key, menu_items in navigation_options.items():
        for item_name, item_keys in menu_items.items():
            if item_keys["allowed"] and st.sidebar.button(
                item_name,
                key=f"nav_{item_keys['page']}",
                type="secondary",
                use_container_width=True,
                disabled=(
                        st.session_state.get("status_connection", None) != "Online"
                        or st.session_state["selected_page"] == item_keys["page"]
                ),
            ):
                st.session_state["selected_page"] = item_keys["page"]
                st.rerun()  # Force immediate rerun

        if any(item["allowed"] for item in menu_items.values()):
            # Add separator
            st.sidebar.divider()

    # System status section
    status_connection = st.session_state.get("status_connection", "Warning")
    st.sidebar.markdown(f"""
    ### 📡 System Status: <span class="status-indicator status-{status_connection.lower()}"></span> {status_connection}
    """, unsafe_allow_html=True)

    return st.session_state["selected_page"]


def main():
    """Main application function"""
    # Apply custom styling
    apply_custom_css()

    # Custom title with styling
    st.sidebar.markdown("""
<div class="nav-title">
    🐱 Cheshire Cat Admin
</div>
""", unsafe_allow_html=True)

    check_status()
    if st.session_state["status_connection"] != "Online":
        st.title("Welcome to the Cheshire Cat Admin UI 🐱")
        st.error("Cheshire Cat backend is offline. Please check your connection.")
        return

    # Add a flag to track if we've attempted cookie check
    st.session_state["token"] = st.session_state.get("token", get_env("CHESHIRE_CAT_API_KEY"))
    st.session_state["initial_auth_check_done"] = st.session_state.get(
        "initial_auth_check_done", st.session_state["token"] is not None,
    )

    if not st.session_state["token"]:
        from app.routes.login import login_page

        # First time: check for cookie without blocking UI
        if not st.session_state["initial_auth_check_done"]:
            # Mark that we've started the check
            st.session_state["initial_auth_check_done"] = True

            # Try to get cookie (async - returns None initially)
            cookie_token = get_cookie("token")
            if cookie_token:
                # If we get a token immediately (rare), use it
                st.session_state["token"] = cookie_token
                time.sleep(1)
                st.rerun()  # Safe rerun now that we have token

            # Most common case: cookie check is async
            # Show loading state instead of login page
            st.sidebar.info("🔍 Checking authentication...")
            # Return a special page key to show loading in main area too
            st.title("Loading...")
            st.info("Checking your authentication status. This will only take a moment.")
            # Optionally add a spinner
            with st.spinner("Checking for saved login..."):
                time.sleep(0.5)  # Brief pause
            return

        # Normal flow continues after initial check
        cookie_token = get_cookie("token")  # Try again after async result
        if cookie_token:
            st.session_state["token"] = cookie_token
            st.rerun()

        st.sidebar.warning("Please log in to access the admin features.")
        time.sleep(1)
        login_page()

        return

    cookie_me = get_cookie_me()

    # Render sidebar navigation and get selected page
    current_page = render_sidebar_navigation(cookie_me)

    if not cookie_me:
        # Add separator
        st.sidebar.divider()

        st.sidebar.info("""You are logged in with the default API key.
    For security reasons, please consider creating admin users and logging in by credentials.""")
    else:
        # logout button
        logout_button = st.sidebar.button("Logout", type="primary", use_container_width=True)
        if logout_button:
            st.session_state["token"] = None
            st.session_state["status_connection"] = "Warning"

            clear_auth_cookies()
            time.sleep(1)  # Wait for cookie to clear

            st.toast("Logged out successfully.", icon="🚪")

            time.sleep(1)  # Wait for a moment before rerunning
            st.rerun()

    if current_page == "chat":
        from app.routes.message import chat

        if "messages" in st.session_state:
            st.session_state.pop("messages", None)

        chat(cookie_me)
        return

    if current_page == "ai_models":
        from app.routes.llms import llms_management

        llms_management(cookie_me)
        return

    if current_page == "auth_handlers":
        from app.routes.auth_handlers import auth_handlers_management

        auth_handlers_management(cookie_me)
        return

    if current_page == "chunkers":
        from app.routes.chunkers import chunkers_management

        chunkers_management(cookie_me)
        return

    if current_page == "embedders":
        from app.routes.embedders import embedders_management

        embedders_management(cookie_me)
        return

    if current_page == "file_handlers":
        from app.routes.file_managers import file_managers_management

        file_managers_management(cookie_me)
        return

    if current_page == "rag":
        from app.routes.rabbit_hole import rabbit_hole_management

        rabbit_hole_management(cookie_me)
        return

    if current_page == "plugins":
        from app.routes.admins.plugins import admin_plugins_management

        admin_plugins_management(cookie_me)
        return

    if current_page == "users":
        from app.routes.users import users_management

        users_management(cookie_me)
        return

    if current_page == "vector_databases":
        from app.routes.vector_databases import vector_databases_management

        vector_databases_management(cookie_me)
        return

    if current_page == "memory":
        from app.routes.memories import memory_management

        memory_management(cookie_me)
        return

    if current_page == "system":
        from app.routes.utilities import utilities_management

        utilities_management(cookie_me)
        return

    # show a welcome message if no page is selected
    st.title("Welcome to the Cheshire Cat Admin UI 🐱")
    if not cookie_me:
        st.markdown("Use the sidebar to navigate through different sections of the admin interface.")
    else:
        st.markdown("Select an agent from the dropdown below to get started.")
        build_agents_select("main", cookie_me)

        # Trigger reload when agent is selected
        if st.session_state.get("agent_id"):
            st.rerun()


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
