# Streamlit Prisoner Management Dashboard with Google Vision OCR
# Save as: Home.py
# Run with: streamlit run Home.py

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os




# CUSTOM CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
    }
    .section-header {
        color: #444;
        border-bottom: 2px solid #667eea;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }
    .success-box {
        padding: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-box {
        padding: 10px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

#HEADER
# Page config
st.set_page_config(
    page_title="Prisoner Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Main dashboard
st.markdown('<div class="main-header"><h1>📊 California Prisoner Outreach Program</h1><p>Secure data management with OCR integration</p></div>', unsafe_allow_html=True)


# LOADING DATA FILE
# Sample fallback data
sample_data = {
    'fName': ['John', 'Jane', 'Bob'],
    'lName': ['Doe', 'Smith', 'Johnson'],
    'CDCRno': ['A123456', 'B789012', 'C345678'],
    'Sponsor': ['Alice T', 'Dave R', 'Alice T'],
    'Stage': [12, 11, 12],
    'city': ['Los Angeles', 'San Diego', 'Oakland'],
    'state': ['CA', 'CA', 'CA'],
    'zip': [90001, 92101, 94601]
}

# Cached loader
@st.cache_data
def load_excel(file):
    return pd.read_excel(file)

# File uploader
uploaded_file = st.file_uploader("📤 Upload Excel File", type=["xlsx"])

# Load data
if uploaded_file:
    df = load_excel(uploaded_file)
    filename = uploaded_file.name
    st.markdown(f"### 📁 **Loaded File:** `{filename}`")
    st.markdown(f"📈 **Total records loaded:** {len(st.session_state.df)}")
else:
    df = pd.DataFrame(sample_data)
    st.info("Using sample data. Upload an Excel file to replace it.")

# Store in session state
st.session_state.df = df



#SOMETHING
# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = load_data()


# SIDEBAR DISPLAY
# Display current database info in Sidebar


st.sidebar.metric("Total Records", len(st.session_state.df))
st.sidebar.metric("Today's date", datetime.now().strftime("%d %b %Y"))
st.sidebar.metric("Time", datetime.now().strftime("%H:%M"))


# DATA SUMMARY BEGINS

#Confidential notification
st.markdown("""
<div style='text-align: center;'>
    <span style='color: red; font-size: 24px; font-weight: bold;'>CONFIDENTIAL</span>
</div>
""", unsafe_allow_html=True)



st.markdown("---")

# ACTIVE SPONSOR COUNT
# Ensure Stage is numeric
st.session_state.df['Stage'] = pd.to_numeric(st.session_state.df['Stage'], errors='coerce')

# Filter active sponsees
active_df = st.session_state.df[st.session_state.df['Stage'] == 12]

# Count unique sponsors and total active sponsees
num_active_sponsors = active_df['Sponsor'].nunique()
num_active_sponsees = active_df.shape[0]

# Display summary
st.markdown(f"### 📊 Active Sponsorship Count")
st.markdown(f"- 🧑‍🤝‍🧑 **Sponsors with active sponsees:** {num_active_sponsors}")
st.markdown(f"- 📋 **Total active sponsees (Stage 12):** {num_active_sponsees}")
st.dataframe(active_df['Sponsor'].value_counts().rename("Active Sponsees"))

# Display same summary data in sidebar
st.sidebar.markdown("---")
st.sidebar.metric(label="Active Sponsors", value=num_active_sponsors)
st.sidebar.metric(label="Active Sponsees", value=num_active_sponsees)



# SPONSOR SPECIFIC DATA
st.markdown("### 🔍 Filter Active Sponsees by Sponsor")
# Filter by Sponsor and Stage == 12, excluding nulls
# Ensure Stage is numeric
st.session_state.df['Stage'] = pd.to_numeric(st.session_state.df['Stage'], errors='coerce')

# Filter sponsors with at least one Stage == 12
eligible_sponsors = st.session_state.df[
    st.session_state.df['Stage'] == 12
]['Sponsor'].dropna().unique()

# Dropdown only shows eligible sponsors
selected_sponsor = st.selectbox(
    "Choose a Sponsor (Stage = 12 only)",
    eligible_sponsors,
    key="choose_sponsor_stage12_home"
)

# Final filtered DataFrame
filtered_df = st.session_state.df[
    (st.session_state.df['Sponsor'] == selected_sponsor) &
    (st.session_state.df['Stage'] == 12)
]

record_count = filtered_df.shape[0]

if record_count > 0:
    st.markdown(f"**📦 Active sponsees found:** {record_count} for `{selected_sponsor}`:")
    st.dataframe(filtered_df)
else:
    st.warning(f"No active sponsees found for `{selected_sponsor}`.")



# SUMMARY STATISTICS
st.markdown("### Summary Statistics")
st.dataframe(st.session_state.df.describe(include='all').transpose())

# PREVIEW ALL DATA
st.markdown("### Preview Total Data")
n = st.slider("Rows to preview", 5, 50, 10)
st.dataframe(st.session_state.df.head(n))


#Confidential notification
st.markdown("""
<div style='text-align: center;'>
    <span style='color: red; font-size: 24px; font-weight: bold;'>CONFIDENTIAL</span>
</div>
""", unsafe_allow_html=True)