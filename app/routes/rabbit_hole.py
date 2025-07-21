import os
import tempfile
import streamlit as st
from cheshirecat_python_sdk import CheshireCatClient
import json

from app.constants import CLIENT_CONFIGURATION
from app.utils import build_agents_select


def upload_files(agent_id: str):
    def add_file_pair():
        st.session_state.file_metadata_pairs.append({"file": None, "metadata": "{}"})

    def remove_file_pair(index):
        st.session_state.file_metadata_pairs.pop(index)
        if not st.session_state.file_metadata_pairs:
            add_file_pair()

    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Upload Files")

    allowed_file_types = client.rabbit_hole.get_allowed_mime_types(agent_id)
    st.markdown(f"""**Allowed file types**: {', '.join(allowed_file_types.allowed)}""")

    if "file_metadata_pairs" not in st.session_state:
        st.session_state.file_metadata_pairs = [{"file": None, "metadata": "{}"}]
    if "remove_index" not in st.session_state:
        st.session_state.remove_index = None

    #  Add file button outside the form
    cols = st.columns([4, 1])
    with cols[0]:
        st.write("### Files to upload")
    with cols[1]:
        if st.button("➕ Add file"):
            add_file_pair()
            st.rerun()  # Refresh to show the new file input

    if st.session_state.remove_index is not None:
        del st.session_state.file_metadata_pairs[st.session_state.remove_index]
        st.session_state.remove_index = None
        st.rerun()

    with st.form("upload_files_form"):
        # Display each file-metadata pair
        for i, pair in enumerate(st.session_state.file_metadata_pairs):
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
                if len(st.session_state.file_metadata_pairs) > 1:
                    if st.form_submit_button(f"❌ Remove this file (#{i+1})", help="Check to remove this file from the upload list"):
                        st.session_state.remove_index = i
                        st.rerun()

        submitted = st.form_submit_button("📤 Upload Files")
        if submitted:
            file_paths = []
            metadata_dict = {}
            has_errors = False
            temp_files = []  # Keep track of temporary files for cleanup

            for i, pair in enumerate(st.session_state.file_metadata_pairs):
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

            if not has_errors and file_paths:
                try:
                    response = client.rabbit_hole.post_files(
                        file_paths=file_paths,
                        agent_id=agent_id,
                        metadata=metadata_dict,
                    )
                    st.toast(f"Successfully uploaded {len(file_paths)} files!", icon="✅")
                    st.json(response.model_dump())
                    # Clear the files after successful upload
                    st.session_state.file_metadata_pairs = [{"file": None, "metadata": "{}"}]
                except Exception as e:
                    st.toast(f"Error uploading files: {e}", icon="❌")
                finally:
                    # Clean up temporary files
                    for temp_file_path in temp_files:
                        try:
                            os.unlink(temp_file_path)
                        except OSError:
                            pass  # Ignore cleanup errors


def upload_url(agent_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Upload from URL")

    with st.form("upload_url_form"):
        url = st.text_input(
            "Website URL",
            placeholder="https://example.com"
        )

        metadata = st.text_area(
            "Metadata (JSON format)",
            value="{}",
            help="Enter metadata to be stored with the content"
        )

        submitted = st.form_submit_button("Upload URL")
        if submitted:
            try:
                metadata_dict = json.loads(metadata)
                response = client.rabbit_hole.post_web(
                    web_url=url,
                    agent_id=agent_id,
                    metadata=metadata_dict
                )
                st.toast(f"URL {url} is being ingested!", icon="✅")
                st.json(response.model_dump())
            except json.JSONDecodeError:
                st.toast("Invalid JSON format in metadata", icon="❌")
            except Exception as e:
                st.toast(f"Error uploading URL: {e}", icon="❌")


def list_files(agent_id: str):
    client = CheshireCatClient(CLIENT_CONFIGURATION)
    st.header("Uploaded Files")

    try:
        files = client.file_manager.get_file_manager_attributes(agent_id)

        # print the total size and number of files
        st.write(f"**Total files uploaded**: {len(files.files)}")
        st.write(f"**Total size of uploaded files**: {files.size} bytes")

        for file in files.files:
            with st.expander(f"{file.name} ({file.size} bytes)"):
                st.write(f"**Name**: {file.name}")
                st.write(f"**Size**: {file.size}")
                st.write(f"**Last modified**: {file.last_modified}")
    except Exception as e:
        st.error(f"Error fetching files: {e}")


def rabbit_hole_management(container):
    st.title("Knowledge Base Management")

    with container:
        build_agents_select()
    if "agent_id" in st.session_state:
        agent_id = st.session_state.agent_id

        menu_options = {
            "(Select a menu)": None,
            "Upload Files": "upload_files",
            "Upload from URL": "upload_url",
            "View Uploaded Files": "list_files",
        }
        choice = st.selectbox("Menu", menu_options)

        if menu_options[choice] == "upload_files":
            upload_files(agent_id)
        elif menu_options[choice] == "upload_url":
            upload_url(agent_id)
        elif menu_options[choice] == "list_files":
            list_files(agent_id)
