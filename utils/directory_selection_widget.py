"""
Directory Selection Widget for Streamlit Applications
"""
import streamlit as st


def directory_selection_widget():
    """
    Creates a directory selection dropdown widget for reference purposes.
    
    This widget displays common directories as a reference guide for users,
    since Streamlit's file_uploader cannot set default directories.
    
    It works for wsl, local host paths seen in popup folder selectors, not absolute reference paths used in linux.

    Returns:
        str: The selected directory path for reference
    """
    # Common directories for reference (using absolute paths for WSL reliability)
    common_directories = {
        "Parent Directory: projects":"\\\\wsl.localhost\\Ubuntu\\home\\me-linux3\\projects",   #"",
        "Project Root: sponsor_dashboard": "\\\\wsl.localhost\\Ubuntu\\home\\me-linux3\\projects\\sponsor_dashboard",
        "CalPOP (Windows)": "E:\\OneDrive - teKnoculture\\CODING\\CalPOP",
        "Letters by Rey/Course (Windows): to prisoners\course_students": "E:\\OneDrive - teKnoculture\\SAA\\CA_prisoners\\to prisoners\\course_students",
        "Windows Screenshots: ": "E:\\OneDrive\\Pictures\\Screenshots",
        "Scanned envelopes for OCR (testing folder)": "E:\\OneDrive - teKnoculture\\CODING\\CalPOP\\automate\\data",
        "Saved PDFs: saved_pdfs": "\\\\wsl.localhost\\Ubuntu\\home\\me-linux3\\projects\\sponsor_dashboard\\saved_pdfs",
        "Downloaded files": "C:\\Users\\rguil\\Downloads"

    }

    st.markdown("### 📁 Directory Selection")
    selected_directory = st.selectbox(
        "Select a common directory (for reference only):",
        list(common_directories.keys()),
        index=0
    )

    # Display selected directory path for user guidance
    selected_path = common_directories[selected_directory]
    st.info(f"📁 Cut and paste this reference path: {selected_directory}: `{selected_path}`")
    
    return selected_path
