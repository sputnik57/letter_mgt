import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st

def render_search():
    st.markdown('<h2 class="section-header">🔍 Search & View Records</h2>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        search_term = st.text_input("Search by Last Name:", placeholder="Enter last name")

    with col2:
        search_btn = st.button("Search", type="primary")

    if search_btn and search_term:
        matches = st.session_state.df[
            st.session_state.df['lName'].str.contains(search_term, case=False, na=False)
        ]

        if matches.empty:
            st.error(f"No matches found for '{search_term}'")
        else:
            st.success(f"Found {len(matches)} match(es)")
            st.dataframe(matches, use_container_width=True)

render_search()