import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
    
import streamlit as st
import pandas as pd
from core.database import save_data

def render_update_person():
    st.markdown('<h2 class="section-header">✏️ Update Person</h2>', unsafe_allow_html=True)

    # Step 1: Find person
    st.subheader("Step 1: Find Person")
    search_name = st.text_input("Search by Last Name:")

    if search_name:
        matches = st.session_state.df[
            st.session_state.df['lName'].str.contains(search_name, case=False, na=False)
        ]

        if not matches.empty:
            # Step 2: Select person
            options = [f"Row {idx}: {row['fName']} {row['lName']}" for idx, row in matches.iterrows()]
            selected = st.selectbox("Select Person:", options)

            if selected:
                row_idx = int(selected.split(":")[0].replace("Row ", ""))
                current_data = st.session_state.df.iloc[row_idx]

                # Step 3: Update form
                st.subheader("Step 2: Update Information")

                with st.form(f"update_person_{row_idx}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        new_fname = st.text_input("First Name", value=current_data.get("fName", ""))
                        new_lname = st.text_input("Last Name", value=current_data.get("lName", ""))
                        new_cdcr = st.text_input("CDCR Number", value=current_data.get("CDCRno", ""))
                        new_housing = st.text_input("Housing", value=current_data.get("housing", ""))

                    with col2:
                        new_letter_exchange = st.text_area(
                            "Letter Exchange",
                            value=current_data.get("letter exchange (received only)", ""),
                            height=100
                        )

                    update_submitted = st.form_submit_button("Save Changes", type="primary")

                    if update_submitted:
                        df = st.session_state.df
                        df.at[row_idx, 'fName'] = new_fname
                        df.at[row_idx, 'lName'] = new_lname
                        df.at[row_idx, 'CDCRno'] = new_cdcr
                        df.at[row_idx, 'housing'] = new_housing
                        df.at[row_idx, 'letter exchange (received only)'] = new_letter_exchange

                        save_data(df)
                        st.success("✅ Person updated successfully!")
                        st.rerun()

render_update_person()