import sys
import os
import re
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Explicitly load .env from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path, override=True)


try:
    from core.ocr import extract_text_from_image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False



def setup_google_credentials():
    """Setup Google Cloud credentials from environment variables"""
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if cred_path and os.path.exists(cred_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
        return True
    return False

def render_ocr_processing():
    st.markdown('<h2 class="section-header">📄 OCR Document Processing</h2>', unsafe_allow_html=True)
    
    # Check if data is loaded
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame()
        st.warning("⚠️ Please load prisoner data first!")
        st.info("Navigate to the main application to upload your Excel file.")
        return

    # Check OCR availability
    if not OCR_AVAILABLE:
        st.error("❌ OCR functionality not available")
        st.info("The OCR module could not be imported. Please check your installation.")
        return

    st.info("📝 Upload handwritten documents to extract text and match to database records")
    
    # Check credentials
    credentials_available = setup_google_credentials()
    if not credentials_available:
        st.warning("⚠️ Google Cloud credentials not configured")
        st.markdown("### To enable OCR functionality:")
        st.markdown("1. Create a `.env` file in your project root directory")
        st.markdown("2. Add your Google Cloud credentials path:")
        st.code("GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json")
        st.markdown("3. Restart the application")
        return

    uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Document", width=400)

        if st.button("Extract Text with OCR", type="primary"):
            with st.spinner("Processing with Google Vision API..."):
                try:
                    extracted_text = extract_text_from_image(uploaded_file)
                except Exception as e:
                    error_msg = str(e)
                    st.error("❌ OCR Processing Failed!")
                    st.warning(f"Error: {error_msg}")
                    
                    # Specific handling for Google Auth errors
                    if 'invalid_grant' in error_msg or '503' in error_msg:
                        st.markdown("### 🔐 Google Cloud Authentication Issue")
                        st.markdown("**Troubleshooting Steps:**")
                        st.markdown("1. **Verify your service account key file**")
                        st.markdown("2. **Check system time synchronization**")
                        st.markdown("3. **Download a new key from Google Cloud Console**")
                    return

            st.subheader("Extracted Text:")
            st.text_area("OCR Result", extracted_text, height=200)

            # Basic matching logic - improved
            st.subheader("Database Matching:")
            words = extracted_text.split()
            potential_matches = []

            for word in words:
                # Skip very short words that might cause too many false matches
                if len(word) < 3:
                    continue
                
                # Escape special regex characters to prevent regex errors
                escaped_word = re.escape(word)
                
                try:
                    matches = st.session_state.df[
                        st.session_state.df['lName'].str.contains(escaped_word, case=False, na=False)
                    ]
                    if not matches.empty:
                        potential_matches.extend(matches.index.tolist())
                except re.error:
                    # Skip words that still cause regex errors
                    continue

            if potential_matches:
                st.success(f"Found {len(set(potential_matches))} potential matches:")
                matched_records = st.session_state.df.iloc[list(set(potential_matches))]
                st.dataframe(matched_records[['fName', 'lName', 'CDCRno', 'housing']])  # Show relevant columns

                # Create better selectbox options
                select_options = ["None"] + [
                    f"Row {idx}: {row['fName']} {row['lName']} ({row['CDCRno']})"
                    for idx, row in matched_records.iterrows()
                ]
                
                selected_match = st.selectbox(
                    "Select record to update:",
                    select_options
                )

                if selected_match != "None":
                    # Extract row index more safely
                    row_idx = int(selected_match.split(":")[0].replace("Row ", ""))
                    
                    if st.button("Update Letter Exchange", type="secondary"):
                        # Handle NaN values in letter exchange
                        current_exchange = st.session_state.df.iloc[row_idx]['letter exchange (received only)']
                        if pd.isna(current_exchange):
                            current_exchange = ""
                        
                        new_entry = f"{datetime.now().strftime('%Y-%m-%d')}: OCR Document processed"
                        if current_exchange.strip():
                            new_exchange = f"{current_exchange}\n---\n{new_entry}"
                        else:
                            new_exchange = new_entry
                            
                        st.session_state.df.at[row_idx, 'letter exchange (received only)'] = new_exchange
                        st.success("✅ Letter exchange updated!")
                        st.rerun()
            else:
                st.warning("No database matches found")

render_ocr_processing()
