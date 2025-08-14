# Streamlit Prisoner Management Dashboard with Google Vision OCR
# Save as: streamlit_app.py
# Run with: streamlit run streamlit_app.py

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os

# Uncomment when you have Google Vision set up:
from google.cloud import vision
import base64

# Page config
st.set_page_config(
    page_title="Prisoner Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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

# Load data function
@st.cache_data
def load_data():
    try:
        df = pd.read_excel('../prisoner_13Aug2025.xlsx')
        return df
    except FileNotFoundError:
        # Create sample data if file doesn't exist
        sample_data = {
            'fName': ['John', 'Jane', 'Bob'],
            'lName': ['Doe', 'Smith', 'Johnson'],
            'CDCRno': ['A123456', 'B789012', 'C345678'],
            'housing': ['Block A', 'Block B', 'Block C'],
            'letter exchange (received only)': ['', '', '']
        }
        return pd.DataFrame(sample_data)

# Caesar cipher function
def caesar_code(first, last, no, s=1):
    first, last = str(first).upper(), str(last).upper()
    if len(first) < 2 or len(last) < 1 or len(str(no)) < 3:
        return "Error: Invalid input"
    
    try:
        a = chr((ord(first[0])+s-65)%26+65)
        b = chr((ord(first[1])+s-65)%26+65)
        c = chr((ord(last[0])+s-65)%26+65)
        d = chr(ord(str(no)[-3]))
        e = chr((ord(str(no)[-2])-s-48)%10+48)
        f = chr((ord(str(no)[-1])-s-48)%10+48)
        return a+b+c+d+e+f
    except:
        return "Error: Unable to generate code"

# Google Vision OCR function (mock for now)
def extract_text_from_image(image_file):
    # Mock function - replace with actual Google Vision API call
  
    # Uncomment and configure when you have Google Vision set up:
    
    client = vision.ImageAnnotatorClient()
    content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    if texts:
        return texts[0].description
    else:
        return "No text found"

    return "Mock OCR Result: Sample extracted text from handwritten document"

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# Main dashboard
st.markdown('<div class="main-header"><h1>📊 California Prisoner Outreach Program</h1><p>Secure data management with OCR integration</p></div>', unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a function:",
    ["🔍 Search & View", "➕ Add New Person", "✏️ Update Person", "🔐 Generate Code", "📄 OCR Processing", "💾 Save Data"]
)

# Display current database info
st.sidebar.markdown("---")
st.sidebar.metric("Total Records", len(st.session_state.df))
st.sidebar.metric("Last Updated", datetime.now().strftime("%H:%M"))

# Page content
if page == "🔍 Search & View":
    st.markdown('<h2 class="section-header">🔍 Search & View Records</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("Search by Last Name:", placeholder="Enter last name")
    
    with col2:
        search_btn = st.button("Search", type="primary")
    
    if search_btn and search_term:
        matches = st.session_state.df[st.session_state.df['lName'].str.contains(search_term, case=False, na=False)]
        
        if matches.empty:
            st.error(f"No matches found for '{search_term}'")
        else:
            st.success(f"Found {len(matches)} match(es)")
            st.dataframe(matches, use_container_width=True)

elif page == "➕ Add New Person":
    st.markdown('<h2 class="section-header">➕ Add New Person</h2>', unsafe_allow_html=True)
    
    with st.form("add_person"):
        col1, col2 = st.columns(2)
        
        with col1:
            fname = st.text_input("First Name*")
            lname = st.text_input("Last Name*")
            cdcr = st.text_input("CDCR Number*")
            housing = st.text_input("Housing")
            address = st.text_input("Address")
            
        with col2:
            city = st.text_input("City")
            state = st.text_input("State")
            zip_code = st.text_input("ZIP Code")
            language = st.text_input("Language")
            sponsor = st.text_input("Sponsor")
        
        submitted = st.form_submit_button("Add Person", type="primary")
        
        if submitted:
            if fname and lname and cdcr:
                new_row = {
                    'fName': fname, 'lName': lname, 'CDCRno': cdcr,
                    'housing': housing, 'address': address, 'city': city,
                    'state': state, 'zip': zip_code, 'language': language,
                    'Sponsor': sponsor, 'letter exchange (received only)': ''
                }
                
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("✅ Person added successfully!")
                st.rerun()
            else:
                st.error("Please fill in required fields (marked with *)")

elif page == "✏️ Update Person":
    st.markdown('<h2 class="section-header">✏️ Update Person</h2>', unsafe_allow_html=True)
    
    # Step 1: Find person
    st.subheader("Step 1: Find Person")
    search_name = st.text_input("Search by Last Name:")
    
    if search_name:
        matches = st.session_state.df[st.session_state.df['lName'].str.contains(search_name, case=False, na=False)]
        
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
                        new_fname = st.text_input("First Name", value=str(current_data['fName']) if pd.notna(current_data['fName']) else "")
                        new_lname = st.text_input("Last Name", value=str(current_data['lName']) if pd.notna(current_data['lName']) else "")
                        new_cdcr = st.text_input("CDCR Number", value=str(current_data['CDCRno']) if pd.notna(current_data['CDCRno']) else "")
                        new_housing = st.text_input("Housing", value=str(current_data['housing']) if pd.notna(current_data['housing']) else "")
                    
                    with col2:
                        new_letter_exchange = st.text_area("Letter Exchange", 
                                                         value=str(current_data['letter exchange (received only)']) if pd.notna(current_data['letter exchange (received only)']) else "",
                                                         height=100)
                    
                    update_submitted = st.form_submit_button("Save Changes", type="primary")
                    
                    if update_submitted:
                        st.session_state.df.iloc[row_idx, st.session_state.df.columns.get_loc('fName')] = new_fname
                        st.session_state.df.iloc[row_idx, st.session_state.df.columns.get_loc('lName')] = new_lname
                        st.session_state.df.iloc[row_idx, st.session_state.df.columns.get_loc('CDCRno')] = new_cdcr
                        st.session_state.df.iloc[row_idx, st.session_state.df.columns.get_loc('housing')] = new_housing
                        st.session_state.df.iloc[row_idx, st.session_state.df.columns.get_loc('letter exchange (received only)')] = new_letter_exchange
                        
                        st.success("✅ Person updated successfully!")
                        st.rerun()

elif page == "🔐 Generate Code":
    st.markdown('<h2 class="section-header">🔐 Generate Security Code</h2>', unsafe_allow_html=True)
    
    with st.form("caesar_cipher"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
        
        with col2:
            number = st.text_input("Number (at least 3 digits)")
            shift = st.number_input("Shift Value", value=1, min_value=1, max_value=25)
        
        generate_btn = st.form_submit_button("Generate Code", type="primary")
        
        if generate_btn:
            if first_name and last_name and number:
                code = caesar_code(first_name, last_name, number, shift)
                if "Error" in code:
                    st.error(code)
                else:
                    st.success(f"Generated Code: **{code}**")
                    st.info(f"Input: {first_name} {last_name}, {number}, shift={shift}")
            else:
                st.error("Please fill in all fields")

elif page == "📄 OCR Processing":
    st.markdown('<h2 class="section-header">📄 OCR Document Processing</h2>', unsafe_allow_html=True)
    
    st.info("📝 Upload handwritten documents to extract text and match to database records")
    
    uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        # Display the image
        st.image(uploaded_file, caption="Uploaded Document", width=400)
        
        if st.button("Extract Text with OCR", type="primary"):
            with st.spinner("Processing with Google Vision API..."):
                # Extract text (using mock function for now)
                extracted_text = extract_text_from_image(uploaded_file)
                
                st.subheader("Extracted Text:")
                st.text_area("OCR Result", extracted_text, height=200)
                
                # Try to match to database
                st.subheader("Database Matching:")
                
                # Simple name extraction (you'd want more sophisticated parsing)
                words = extracted_text.split()
                potential_matches = []
                
                for word in words:
                    matches = st.session_state.df[st.session_state.df['lName'].str.contains(word, case=False, na=False)]
                    if not matches.empty:
                        potential_matches.extend(matches.index.tolist())
                
                if potential_matches:
                    st.success(f"Found {len(set(potential_matches))} potential matches:")
                    matched_records = st.session_state.df.iloc[list(set(potential_matches))]
                    st.dataframe(matched_records)
                    
                    # Option to update letter exchange
                    selected_match = st.selectbox("Select record to update:", 
                                                ["None"] + [f"Row {idx}: {row['fName']} {row['lName']}" 
                                                           for idx, row in matched_records.iterrows()])
                    
                    if selected_match != "None":
                        if st.button("Update Letter Exchange", type="secondary"):
                            row_idx = int(selected_match.split(":")[0].replace("Row ", ""))
                            current_exchange = st.session_state.df.iloc[row_idx]['letter exchange (received only)']
                            new_exchange = f"{current_exchange}\n---\n{datetime.now().strftime('%Y-%m-%d')}: OCR Document processed"
                            st.session_state.df.iloc[row_idx, st.session_state.df.columns.get_loc('letter exchange (received only)')] = new_exchange
                            st.success("✅ Letter exchange updated!")
                            st.rerun()
                else:
                    st.warning("No database matches found")

elif page == "💾 Save Data":
    st.markdown('<h2 class="section-header">💾 Save Data</h2>', unsafe_allow_html=True)
    
    filename = st.text_input("Filename:", value="prisoner_data_updated.xlsx")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save to Excel", type="primary"):
            try:
                if not filename.endswith('.xlsx'):
                    filename += '.xlsx'
                
                st.session_state.df.to_excel(filename, index=False)
                st.success(f"✅ Data saved successfully to {filename}")
                st.info(f"📊 Records saved: {len(st.session_state.df)}")
            except Exception as e:
                st.error(f"❌ Error saving file: {e}")
    
    with col2:
        # Download button
        csv_buffer = io.StringIO()
        st.session_state.df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv_buffer.getvalue(),
            file_name="prisoner_data.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown(f"📈 **Dashboard Status:** {len(st.session_state.df)} records loaded | Last updated: {datetime.now().strftime('%H:%M:%S')}")