# pdf_envelopes_app.py
import streamlit as st
import pandas as pd
import cairo
from io import BytesIO
import time

# Function defining PDF paper size, layout and text format
INCHES_TO_POINTS = 72

def write_envelopes_buffer(from_addr, to_addrs):
    """Write envelopes to a BytesIO buffer."""
    buffer = BytesIO()
    surface = cairo.PDFSurface(buffer,
                               9.5 * INCHES_TO_POINTS,
                               4.13 * INCHES_TO_POINTS)
    cr = cairo.Context(surface)
    cr.select_font_face('serif')

    MARGIN = 0.30
    for to_addr in to_addrs:
        # Write return address
        for i, line in enumerate(from_addr):
            cr.move_to(MARGIN * INCHES_TO_POINTS,
                       (MARGIN * INCHES_TO_POINTS) + 12 + (12 * i))
            cr.show_text(line)

        # Write recipient address
        for i, line in enumerate(to_addr):
            cr.move_to(4.5 * INCHES_TO_POINTS,
                       (2.25 * INCHES_TO_POINTS) + 30 + (12 * i))
            cr.show_text(line)
        cr.show_page()

    surface.flush()
    surface.finish()
    buffer.seek(0)
    return buffer

def process_prisoner_data(df, selected_records):
    """Process prisoner data and generate address lists."""
    # Use only selected records
    sponsList = selected_records.copy()
    
    # Reduce dataframe to relevant columns only
    sponsList2 = sponsList[['fName', 'lName', 'Unsafe?', 'CDCRno', 'housing', 'address', 'city', 'state', 'zip']].copy()
    
    # Merge name and location columns
    sponsList2['Name'] = sponsList2[['fName', 'lName', 'CDCRno']].astype(str).agg(' '.join, axis=1)
    sponsList2['location'] = sponsList2[['city', 'state']].astype(str).agg(' '.join, axis=1) + ' ' + sponsList2['zip'].astype(str)
    
    # Remove redundant columns that were merged
    sponsList2 = sponsList2[['Name', 'housing', 'address', 'location', 'Unsafe?']]
    
    # Separate safe and unsafe environments
    KEYWORD = "unsafe"
    unsafe_env = sponsList2['Unsafe?'].str.casefold().isin([KEYWORD])
    sponsList2_unsafe = sponsList2[unsafe_env]
    sponsList2_safe = sponsList2[~unsafe_env]
    
    # Handle empty data cases
    if len(sponsList2_unsafe) > 0:
        sponsList2_unsafe.fillna(' ', inplace=True)
    sponsList2_safe.fillna(' ', inplace=True)
    
    # Prepare envelope lists
    sponsList3_unsafe = []
    if len(sponsList2_unsafe) > 0:
        sponsList3_unsafe = sponsList2_unsafe.drop(['Unsafe?'], axis=1)
        sponsList3_unsafe = sponsList3_unsafe.values.tolist()
    
    sponsList3_safe = sponsList2_safe.drop(['Unsafe?'], axis=1)
    sponsList3_safe = sponsList3_safe.values.tolist()
    
    return sponsList3_safe, sponsList3_unsafe

def search_and_select_prisoners(df):
    """Search-as-you-typed prisoner selection system with proper multi-selection tracking"""
    
    st.subheader("2. Search and Select Prisoners")
    
    # Initialize session state for selections
    if 'all_selected_indices' not in st.session_state:
        st.session_state.all_selected_indices = set()
    
    # Create a better display name for search - convert all to string first
    df['search_display'] = (
        df['lName'].fillna('').astype(str) + ", " + 
        df['fName'].fillna('').astype(str) + 
        " (" + df['housing'].fillna('').astype(str) + ")" +
        " [" + df['CDCRno'].fillna('No ID').astype(str) + "]"
    )
    
    # Show all currently selected prisoners
    if st.session_state.all_selected_indices:
        st.markdown("#### ✅ Currently Selected Prisoners")
        currently_selected_df = df[df.index.isin(st.session_state.all_selected_indices)]
        st.dataframe(currently_selected_df[['fName', 'lName', 'CDCRno', 'housing', 'Unsafe?']])
        st.markdown(f"**Total selected: {len(st.session_state.all_selected_indices)}**")
        st.markdown("---")
    
    # Clear instructions for search
    st.markdown("#### 🔍 Search for Prisoners")
    st.markdown("Type a last name, first name, ID number, or housing to find prisoners:")
    
    # Prominent search box
    search_term = st.text_input(
        "Enter search term:",
        placeholder="e.g., Smith, John, A12345, Facility A",
        key="prisoner_search"
    )
    
    # Filter based on search term
    if search_term and len(search_term) >= 2:  # Only search if 2+ characters
        search_term_lower = search_term.lower()
        
        # Build search conditions - check if columns exist before using them
        conditions = [
            df['lName'].astype(str).str.lower().str.contains(search_term_lower, na=False),
            df['fName'].astype(str).str.lower().str.contains(search_term_lower, na=False),
            df['CDCRno'].astype(str).str.lower().str.contains(search_term_lower, na=False),
            df['housing'].astype(str).str.lower().str.contains(search_term_lower, na=False)
        ]
        
        # Only include folderCode in search if it exists
        if 'folderCode' in df.columns:
            conditions.append(df['folderCode'].astype(str).str.lower().str.contains(search_term_lower, na=False))
        
        # Combine all conditions
        combined_condition = conditions[0]
        for condition in conditions[1:]:
            combined_condition = combined_condition | condition
            
        filtered_df = df[combined_condition]
        st.info(f"Found {len(filtered_df)} matching prisoners")
    elif search_term and len(search_term) < 2:
        st.info("Please enter at least 2 characters to search...")
        filtered_df = pd.DataFrame()
    else:
        # Show instruction when no search
        st.info("👆 Start typing in the search box above to find prisoners")
        st.markdown("**Example searches:**")
        st.markdown("- Last name: `Smith`")
        st.markdown("- First name: `John`") 
        st.markdown("- ID number: `A12345`")
        st.markdown("- Housing: `Facility A`")
        filtered_df = pd.DataFrame()
    
    # Show matching prisoners for selection
    if not filtered_df.empty and len(filtered_df) > 0:
        st.markdown("#### 📋 Select Prisoners (Current Search)")
        
        # Track which indices are selected in current search
        current_search_selections = set()
        
        for idx, row in filtered_df.iterrows():
            # Unique key for each checkbox
            checkbox_key = f"select_{idx}"
            
            # Create a clear display for each prisoner - ensure all values are strings
            prisoner_display = (
                f"**{row['lName']}, {row['fName']}** - "
                f"{row['housing']} [{row['CDCRno']}]"
            )
            
            # Show checkbox with prisoner info
            is_selected = st.checkbox(
                prisoner_display,
                key=checkbox_key,
                value=(idx in st.session_state.all_selected_indices)
            )
            
            # Track current selections
            if is_selected:
                current_search_selections.add(idx)
        
        # Update all selections: Remove indices from current search, then add back selected ones
        # First, remove any indices that were in the current search results
        current_search_indices = set(filtered_df.index)
        st.session_state.all_selected_indices = st.session_state.all_selected_indices - current_search_indices
        
        # Then add back the ones that are currently selected
        st.session_state.all_selected_indices.update(current_search_selections)
        
        # Get ALL selected records (not just current search)
        if st.session_state.all_selected_indices:
            selected_records = df[df.index.isin(st.session_state.all_selected_indices)]
            
            # Save to session state
            st.session_state.selected_records = selected_records
            return selected_records
        else:
            # Return previously selected if they exist
            if 'selected_records' in st.session_state:
                return st.session_state.selected_records
    else:
        # No matches or no search yet - show existing selections
        if 'selected_records' in st.session_state and st.session_state.all_selected_indices:
            return st.session_state.selected_records
    
    return pd.DataFrame()

def load_data_page():
    """Page for loading and caching prisoner data"""
    st.subheader("1. Upload Prisoner Data")
    uploaded_file = st.file_uploader(
        "Choose Excel file with prisoner data",
        type=["xlsx"],
        key="excel_uploader"
    )
    
    if uploaded_file is not None:
        try:
            # Read the Excel file
            pris_file = pd.read_excel(uploaded_file, sheet_name='Sheet1')
            st.success("File successfully loaded!")
            
            # Cache the data in session state
            st.session_state.pris_file = pris_file
            st.session_state.data_loaded = True
            st.session_state.file_name = uploaded_file.name
            
            # Show data preview
            with st.expander("Preview Prisoner Data"):
                st.dataframe(pris_file.head(10))
                
            st.info("Data loaded and cached! You can now navigate to other pages.")
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please ensure your Excel file has the required columns: fName, lName, Unsafe?, CDCRno, housing, address, city, state, zip")
    else:
        st.info("Please upload an Excel file to get started")
        
        # Show example of expected format
        with st.expander("See expected data format"):
            example_data = pd.DataFrame({
                'fName': ['John', 'Jane'],
                'lName': ['Doe', 'Smith'],
                'Unsafe?': ['', 'unsafe'],
                'CDCRno': ['A12345', 'B67890'],
                'housing': ['Facility A-101', 'Facility B-202'],
                'address': ['123 Main St', 'PO Box 456'],
                'city': ['Los Angeles', 'San Francisco'],
                'state': ['CA', 'CA'],
                'zip': ['90001', '94102']
            })
            st.dataframe(example_data)

def select_prisoners_page():
    """Page for selecting prisoners from cached data"""
    if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
        st.warning("Please load prisoner data first!")
        st.info("Navigate to the 'Load Data' page to upload your Excel file.")
        return
    
    st.subheader(f"Loaded Data: {st.session_state.file_name}")
    
    # Show data info
    pris_file = st.session_state.pris_file
    st.write(f"Total prisoners in database: {len(pris_file)}")
    
    # Use search-as-you-type selector
    selected_prisoners = search_and_select_prisoners(pris_file)
    
    if not selected_prisoners.empty:
        # Cache selected prisoners
        st.session_state.selected_prisoners = selected_prisoners
        st.session_state.prisoners_selected = True
        
        st.success(f"Selected {len(selected_prisoners)} prisoners!")
        st.markdown("---")
        if st.button("📝 Generate Envelopes", type="primary"):
            st.session_state.current_page = "Generate Envelopes"
            st.rerun()

def generate_envelopes_page():
    """Page for generating envelopes from selected prisoners"""
    if 'prisoners_selected' not in st.session_state or not st.session_state.prisoners_selected:
        st.warning("Please select prisoners first!")
        st.info("Navigate to the 'Select Prisoners' page to choose prisoners.")
        return
    
    st.subheader("🖨️ Generate Envelopes")
    
    # Show selected prisoners
    selected_prisoners = st.session_state.selected_prisoners
    st.markdown(f"### Selected Prisoners ({len(selected_prisoners)} total)")
    st.dataframe(selected_prisoners[['fName', 'lName', 'CDCRno', 'housing', 'Unsafe?']])
    
    # Show breakdown by safety classification
    unsafe_count = len(selected_prisoners[selected_prisoners['Unsafe?'].str.lower().str.contains('unsafe', na=False)])
    safe_count = len(selected_prisoners) - unsafe_count
    
    st.markdown("### Envelope Classification")
    col1, col2 = st.columns(2)
    col1.metric("_SAFE Environment_", safe_count)
    col2.metric("_UNSAFE Environment_", unsafe_count)
    
    st.markdown("---")
    st.markdown("#### Preview of Envelope Generation")
    st.info("This will generate two PDF files:")
    st.markdown("- **Safe Environment Envelopes** (for most prisoners)")
    st.markdown("- **Unsafe Environment Envelopes** (only if needed)")
    
    if st.button("🖨️ Create Envelopes", type="primary"):
        with st.spinner("Processing data and generating PDFs..."):
            # Process prisoner data
            safe_list, unsafe_list = process_prisoner_data(st.session_state.pris_file, selected_prisoners)
            
            # Generate timestamp
            timestamp = time.strftime("%Y%m%d-%H%M")
            
            # Create unsafe envelopes (if any)
            if len(unsafe_list) > 0:
                FROM_ADDR_UNSAFE = ('Calif. Prisoner Outreach Program',
                                    'PO Box 57648',
                                    'Sherman Oaks, CA 91413')
                unsafe_pdf = write_envelopes_buffer(FROM_ADDR_UNSAFE, unsafe_list)
                
                st.download_button(
                    label="📥 Download Unsafe Environment Envelopes",
                    data=unsafe_pdf,
                    file_name=f'envelopes_unsafe_{timestamp}.pdf',
                    mime="application/pdf",
                    key="unsafe_download"
                )
            
            # Create safe envelopes
            FROM_ADDR_SAFE = ('SCISAA',
                              'PO Box 57648',
                              'Sherman Oaks, CA 91413',
                              'Attn: Calif. Prisoner Outreach Program')
            safe_pdf = write_envelopes_buffer(FROM_ADDR_SAFE, safe_list)
            
            st.download_button(
                label="📥 Download Safe Environment Envelopes",
                data=safe_pdf,
                file_name=f'envelopes_safe_{timestamp}.pdf',
                mime="application/pdf",
                key="safe_download"
            )
            
            # Summary
            st.subheader("✅ Generation Complete")
            col1, col2 = st.columns(2)
            col1.metric("Safe Environment Envelopes", len(safe_list))
            if len(unsafe_list) > 0:
                col2.metric("Unsafe Environment Envelopes", len(unsafe_list))
            else:
                col2.metric("Unsafe Environment Envelopes", 0)
            
            st.success("PDFs generated successfully! Use the download buttons above.")

def main():
    st.set_page_config(
        page_title="Prisoner Envelope Generator",
        page_icon="✉️",
        layout="wide"
    )
    
    st.title("✉️ Prisoner Envelope Generator")
    st.markdown("""
    Generate PDF envelopes for prisoner correspondence with different return addresses 
    based on environment safety classification.
    """)
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Load Data"
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'prisoners_selected' not in st.session_state:
        st.session_state.prisoners_selected = False
    
    # Navigation
    st.sidebar.title("Navigation")
    pages = ["Load Data", "Select Prisoners", "Generate Envelopes"]
    
    # Create navigation buttons
    for page in pages:
        if st.sidebar.button(page, 
                           key=f"nav_{page}",
                           type="primary" if st.session_state.current_page == page else "secondary"):
            st.session_state.current_page = page
            st.rerun()
    
    # Display current page
    if st.session_state.current_page == "Load Data":
        load_data_page()
    elif st.session_state.current_page == "Select Prisoners":
        select_prisoners_page()
    elif st.session_state.current_page == "Generate Envelopes":
        generate_envelopes_page()

if __name__ == "__main__":
    main()