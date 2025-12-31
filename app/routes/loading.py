import time
import streamlit as st


def loading_page():
    st.sidebar.info("🔍 Checking authentication...")
    # Return a special page key to show loading in main area too
    st.header("Loading...")
    st.info("Checking your authentication status. This will only take a moment.")
    # Optionally add a spinner
    with st.spinner("Checking for saved login..."):
        time.sleep(0.5)  # Brief pause