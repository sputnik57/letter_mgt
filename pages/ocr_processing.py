import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
from datetime import datetime
from core.ocr import extract_text_from_image
import pandas as pd

def render_ocr_processing():
    st.markdown('<h2 class="section-header">📄 OCR Document Processing</h2>', unsafe_allow_html=True)
    st.info("📝 Upload handwritten documents to extract text and match to database records")

    uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Document", width=400)

        if st.button("Extract Text with OCR", type="primary"):
            with st.spinner("Processing with Google Vision API..."):
                extracted_text = extract_text_from_image(uploaded_file)

            st.subheader("Extracted Text:")
            st.text_area("OCR Result", extracted_text, height=200)

            # Basic matching logic
            st.subheader("Database Matching:")
            words = extracted_text.split()
            potential_matches = []

            for word in words:
                matches = st.session_state.df[
                    st.session_state.df['lName'].str.contains(word, case=False, na=False)
                ]
                if not matches.empty:
                    potential_matches.extend(matches.index.tolist())

            if potential_matches:
                st.success(f"Found {len(set(potential_matches))} potential matches:")
                matched_records = st.session_state.df.iloc[list(set(potential_matches))]
                st.dataframe(matched_records)

                selected_match = st.selectbox(
                    "Select record to update:",
                    ["None"] + [f"Row {idx}: {row['fName']} {row['lName']}"
                                for idx, row in matched_records.iterrows()]
                )

                if selected_match != "None":
                    if st.button("Update Letter Exchange", type="secondary"):
                        row_idx = int(selected_match.split(":")[0].replace("Row ", ""))
                        current_exchange = st.session_state.df.iloc[row_idx]['letter exchange (received only)']
                        new_exchange = f"{current_exchange}\n---\n{datetime.now().strftime('%Y-%m-%d')}: OCR Document processed"
                        st.session_state.df.at[row_idx, 'letter exchange (received only)'] = new_exchange
                        st.success("✅ Letter exchange updated!")
                        st.rerun()
            else:
                st.warning("No database matches found")

render_ocr_processing()