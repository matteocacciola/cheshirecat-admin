import os
import tempfile
import time
from typing import Dict
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient
import json
import base64

from app.utils import build_agents_select, show_overlay_spinner, build_client_configuration


def upload_files(agent_id: str):
    def add_file_pair():
        st.session_state["file_metadata_pairs"].append({"file": None, "metadata": "{}"})

    client = CheshireCatClient(build_client_configuration())
    st.header("Upload Files")

    allowed_file_types = client.rabbit_hole.get_allowed_mime_types(agent_id)
    st.markdown(f"""**Allowed file types**: {', '.join(allowed_file_types.allowed)}""")

    st.session_state["file_metadata_pairs"] = st.session_state.get(
        "file_metadata_pairs", [{"file": None, "metadata": "{}"}],
    )
    st.session_state["remove_index"] = st.session_state.get("remove_index")

    #  Add file button outside the form
    cols = st.columns([4, 1])
    with cols[0]:
        st.write("### Files to upload")
    with cols[1]:
        if st.button("➕ Add file"):
            add_file_pair()
            st.rerun()  # Refresh to show the new file input

    if st.session_state["remove_index"] is not None:
        del st.session_state["file_metadata_pairs"][st.session_state["remove_index"]]
        st.session_state["remove_index"] = None
        st.rerun()

    with st.form("upload_files_form", clear_on_submit=True, enter_to_submit=False):
        # Display each file-metadata pair
        for i, pair in enumerate(st.session_state["file_metadata_pairs"]):
            col1, col2, col3 = st.columns([1, 1, 0.5])
            with col1:
                pair["file"] = st.file_uploader(f"File {i + 1}", key=f"file_{i}")
            with col2:
                pair["metadata"] = st.text_area(
                    f"Metadata {i + 1}",
                    value=pair["metadata"],
                    key=f"metadata_{i}",
                    height=150,
                    help="Enter metadata as JSON for this specific file"
                )
            with col3:
                if len(st.session_state["file_metadata_pairs"]) > 1:
                    if st.form_submit_button(f"❌ Remove this file (#{i+1})", help="Check to remove this file from the upload list"):
                        st.session_state["remove_index"] = i
                        st.rerun()

        if not st.form_submit_button("📤 Upload Files"):
            return

        file_paths = []
        metadata_dict = {}
        has_errors = False
        temp_files = []  # Keep track of temporary files for cleanup

        for i, pair in enumerate(st.session_state["file_metadata_pairs"]):
            if not pair["file"]:
                st.error(f"Please select a file for File {i + 1}")
                has_errors = True
                continue

            try:
                # Validate JSON metadata
                metadata = json.loads(pair["metadata"])

                # Save uploaded file to temporary location
                uploaded_file = pair["file"]
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f"_{uploaded_file.name}"
                )
                temp_file.write(uploaded_file.getbuffer())
                temp_file.close()

                # Add to our lists
                file_paths.append(temp_file.name)
                temp_files.append(temp_file.name)  # For cleanup
                metadata_dict[uploaded_file.name] = metadata
            except json.JSONDecodeError:
                st.error(f"Invalid JSON format in metadata for File {i + 1}")
                has_errors = True

        if has_errors or not file_paths:
            return

        try:
            spinner_container = show_overlay_spinner(f"Loading files to RAG...")

            client.rabbit_hole.post_files(
                file_paths=file_paths,
                agent_id=agent_id,
                metadata=metadata_dict,
            )
            st.toast(f"Successfully uploaded {len(file_paths)} files!", icon="✅")
            # Clear the files after successful upload
            st.session_state["file_metadata_pairs"] = [{"file": None, "metadata": "{}"}]
        except Exception as e:
            st.toast(f"Error uploading files: {e}", icon="❌")
        finally:
            spinner_container.empty()  # Remove the spinner
            # Clean up temporary files
            for temp_file_path in temp_files:
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore cleanup errors


def upload_url(agent_id: str):
    client = CheshireCatClient(build_client_configuration())
    st.header("Upload from URL")

    with st.form("upload_url_form", clear_on_submit=True, enter_to_submit=False):
        url = st.text_input(
            "Website URL",
            placeholder="https://example.com"
        )

        metadata = st.text_area(
            "Metadata (JSON format)",
            value="{}",
            help="Enter metadata to be stored with the content"
        )

        if not st.form_submit_button("Upload URL"):
            return

        try:
            spinner_container = show_overlay_spinner(f"Loading URL to RAG...")

            metadata_dict = json.loads(metadata)
            client.rabbit_hole.post_web(
                web_url=url,
                agent_id=agent_id,
                metadata=metadata_dict
            )
            st.toast(f"URL {url} is being ingested!", icon="✅")
        except json.JSONDecodeError:
            st.toast("Invalid JSON format in metadata", icon="❌")
        except Exception as e:
            st.toast(f"Error uploading URL: {e}", icon="❌")
        finally:
            spinner_container.empty()


def list_files(agent_id: str):
    client = CheshireCatClient(build_client_configuration())
    st.header("Uploaded Files")

    try:
        files = client.file_manager.get_file_manager_attributes(agent_id)

        # print the total size and number of files
        st.write(f"**Total files uploaded**: {len(files.files)}")
        st.write(f"**Total size of uploaded files**: {files.size} bytes")

        for file in files.files:
            col1, col2, col3 = st.columns([0.7, 0.15, 0.15])

            with col1:
                chunks = client.memory.get_memory_points(
                    agent_id=agent_id,
                    collection="declarative",
                    metadata={"source": file.name},
                )

                with st.expander(f"{file.name} ({file.size} bytes)"):
                    st.write(f"**Name**: {file.name}")
                    st.write(f"**Size**: {file.size}")
                    st.write(f"**Last modified**: {file.last_modified}")
                    st.write(f"**Chunks**: {len(chunks.points)}")

            with col2:
                if st.button("Download", key=file.name):
                    try:
                        response = client.file_manager.get_file(agent_id, file.name)

                        # Convert to base64 for JavaScript
                        file_data = base64.b64encode(response.content).decode()

                        # Inject JavaScript to trigger download
                        st.components.v1.html(
                            f"""
                            <script>
                            function downloadFile() {{
                                const link = document.createElement('a');
                                link.href = 'data:application/octet-stream;base64,{file_data}';
                                link.download = '{file.name}';
                                link.click();
                            }}
                            downloadFile();
                            </script>
                            """,
                            height=0
                        )
                        st.toast("Download started!", icon="✅")
                    except Exception as e:
                        st.toast(f"Error downloading file: {e}", icon="❌")

            with col3:
                if st.button("Delete", key=f"delete_{file.name}", help="Permanently delete this file"):
                    st.session_state["file_to_delete"] = file

        # Delete confirmation
        if not (file := st.session_state.get("file_to_delete")):
            return

        st.warning(f"⚠️ Are you sure you want to permanently delete file `{file.name}`?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete File", type="primary"):
                try:
                    spinner_container = show_overlay_spinner(f"Deleting file {file.name}...")

                    client.file_manager.delete_file(agent_id, file.name)
                    st.toast(f"File {file.name} deleted successfully!", icon="✅")
                    st.session_state.pop("file_to_delete", None)
                    time.sleep(1)  # Wait for a moment before rerunning
                except Exception as e:
                    st.error(f"Error deleting admin: {e}", icon="❌")
                finally:
                    spinner_container.empty()

                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.pop("file_to_delete", None)
                st.rerun()
    except Exception as e:
        st.toast(f"Error fetching files: {e}", icon="❌")


def rabbit_hole_management(cookie_me: Dict | None):
    st.title("Knowledge Base Management")

    st.info("""**Disclaimer**: If you want to store the files of the Knowledge Base in a specific file manager,
    please select it in the **File Managers** section and enable the `CCAT_RABBIT_HOLE_STORAGE_ENABLED` environment variable in the CheshireCat.""")

    build_agents_select("rabbit_hole", cookie_me)
    if not (agent_id := st.session_state.get("agent_id")):
        return

    menu_options = {
        "(Select a menu)": None,
        "Upload Files": "upload_files",
        "Upload from URL": "upload_url",
        "View Uploaded Files": "list_files",
    }
    choice = st.selectbox("Menu", menu_options)

    if menu_options[choice] == "upload_files":
        upload_files(agent_id)
        return

    if menu_options[choice] == "upload_url":
        upload_url(agent_id)
        return

    if menu_options[choice] == "list_files":
        list_files(agent_id)
