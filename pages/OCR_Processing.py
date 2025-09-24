import sys
import os
import re
import json
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

try:
    from core.letter_db import LetterDatabase
    LETTER_DB_AVAILABLE = True
except ImportError:
    LETTER_DB_AVAILABLE = False



def setup_google_credentials():
    """Setup Google Cloud credentials from environment variables"""
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if cred_path and os.path.exists(cred_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
        return True
    return False

def render_ocr_processing():
    st.markdown('<h2 class="section-header">OCR Document Processing</h2>', unsafe_allow_html=True)

    # Initialize session state at the very beginning
    if 'selected_prisoner_idx' not in st.session_state:
        st.session_state.selected_prisoner_idx = None
    if 'show_actions' not in st.session_state:
        st.session_state.show_actions = False
    if 'ocr_completed' not in st.session_state:
        st.session_state.ocr_completed = False
    if 'envelope_queue' not in st.session_state:
        st.session_state.envelope_queue = []
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = ""
    if 'return_address' not in st.session_state:
        st.session_state.return_address = ""
    if 'saved_letters' not in st.session_state:
        st.session_state.saved_letters = {}
    
    # Initialize letter database
    letter_db_working = LETTER_DB_AVAILABLE
    if 'letter_db' not in st.session_state and LETTER_DB_AVAILABLE:
        try:
            st.session_state.letter_db = LetterDatabase()
            st.sidebar.success("📋 Letter database connected")
        except Exception as e:
            st.sidebar.error(f"❌ Database error: {e}")
            letter_db_working = False
    
    # Debug info in sidebar
    if letter_db_working and 'letter_db' in st.session_state:
        st.sidebar.write(f"Database: {st.session_state.letter_db.db_path}")
        try:
            letter_count = len(st.session_state.letter_db.get_all_letters())
            st.sidebar.write(f"Letters in DB: {letter_count}")
        except:
            st.sidebar.write("Letters in DB: Error reading")

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
    
    # Display envelope queue status
    if st.session_state.envelope_queue:
        queue_count = len(st.session_state.envelope_queue)
        st.info(f"📋 Envelope Queue: {queue_count} letter{'s' if queue_count != 1 else ''} ready for printing")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("👀 View Queue", type="secondary", use_container_width=True):
                st.subheader("📋 Current Envelope Queue:")
                for i, entry in enumerate(st.session_state.envelope_queue, 1):
                    st.write(f"{i}. **{entry['name']}** (CDCR #{entry['cdcr_no']}) - {entry['timestamp']}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("🗑️ Clear Queue", type="secondary"):
                        st.session_state.envelope_queue = []
                        st.success("✅ Envelope queue cleared!")
                        st.rerun()
                with col_b:
                    if st.button("🖨️ Go to Print Page", type="primary"):
                        st.info("💡 Navigate to 'Print Envelopes' page to process the queue")
    
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

    # Import directory selection widget
    from utils.directory_selection_widget import directory_selection_widget

    # 📁 Select the directory
    directory_selection_widget()

    # Choose input method
    input_method = st.radio("Choose input method:", ["Upload File", "Take Photo with Webcam"])

    uploaded_file = None
    if input_method == "Upload File":
        uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])
    else:
        uploaded_file = st.camera_input("Take a photo of the envelope")

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Document", width=400)

        # Save captured image and raw data to disk
        if input_method == "Take Photo with Webcam":
            # Create images directory if it doesn't exist
            images_dir = os.path.join(project_root, "saved_images")
            os.makedirs(images_dir, exist_ok=True)

            # Save with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"webcam_capture_{timestamp}"
            image_filename = f"{base_filename}.png"
            json_filename = f"{base_filename}.json"
            image_path = os.path.join(images_dir, image_filename)
            json_path = os.path.join(images_dir, json_filename)

            # Save the image
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # Save raw OCR data as JSON (will be saved after OCR processing)
            st.success(f"📸 Image saved to: `{image_path}`")
            # Persist for DB autosave even after reruns
            st.session_state.last_image_path = image_path
        elif input_method == "Upload File":
            # Also persist uploaded files to disk so Letter Management can reference them
            images_dir = os.path.join(project_root, "saved_images")
            os.makedirs(images_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            orig_name = getattr(uploaded_file, "name", "upload")
            _, ext = os.path.splitext(orig_name)
            if ext.lower() not in [".png", ".jpg", ".jpeg"]:
                ext = ".png"
            base_filename = f"upload_{timestamp}"
            image_filename = f"{base_filename}{ext.lower()}"
            image_path = os.path.join(images_dir, image_filename)

            # Save the uploaded image bytes
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            st.success(f"📸 Image saved to: `{image_path}`")
            # Persist for DB autosave even after reruns
            st.session_state.last_image_path = image_path

        # OCR Processing Button
        if st.button("Extract Text with OCR", type="primary", key="extract_ocr"):
            with st.spinner("Processing with Google Vision API..."):
                try:
                    ocr_result = extract_text_from_image(uploaded_file)
                    if isinstance(ocr_result, dict):
                        extracted_text = ocr_result['full_text']
                        return_address = ocr_result['return_address']
                        raw_response = ocr_result.get('raw_response', {})

                        # Save raw JSON data for webcam captures
                        if input_method == "Take Photo with Webcam" and 'json_path' in locals():
                            try:
                                with open(json_path, 'w', encoding='utf-8') as f:
                                    json.dump(raw_response, f, indent=2, ensure_ascii=False)
                                st.success(f"📄 Raw OCR data saved to: `{json_path}`")
                            except Exception as json_error:
                                st.warning(f"Could not save JSON data: {json_error}")
                    else:
                        # Backward compatibility for string returns
                        extracted_text = ocr_result
                        return_address = "Return address extraction not available"
                        raw_response = {}

                    # Store OCR results in session state
                    st.session_state.extracted_text = extracted_text
                    st.session_state.return_address = return_address if 'return_address' in locals() else ""
                    st.session_state.ocr_completed = True

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
                    st.session_state.ocr_completed = False
                    return

        # Show OCR results and prisoner matching if OCR is completed
        if st.session_state.ocr_completed and 'extracted_text' in st.session_state:
            extracted_text = st.session_state.extracted_text

            # Display the complete OCR text (description from Google Vision)
            st.subheader("Extracted Text:")
            st.text_area("OCR Result", extracted_text, height=250)

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
                    "Select prisoner record:",
                    select_options,
                    key="prisoner_select"
                )

                if selected_match != "None":
                    # Extract row index more safely
                    row_idx = int(selected_match.split(":")[0].replace("Row ", ""))
                    st.session_state.selected_prisoner_idx = row_idx
                    st.session_state.show_actions = True

                    # Auto-save letter to DB once a prisoner is selected (no extra click needed)
                    try:
                        if LETTER_DB_AVAILABLE and 'letter_db' in st.session_state:
                            image_path_to_save = st.session_state.get('last_image_path', None)
                            # Avoid duplicate insert for same image
                            already_saved = image_path_to_save and image_path_to_save in st.session_state.get('saved_letters', {})
                            if image_path_to_save and not already_saved:
                                ocr_data = {
                                    'full_text': st.session_state.get('extracted_text', ''),
                                    'return_address': st.session_state.get('return_address', '')
                                }
                                selected_record = st.session_state.df.iloc[row_idx]
                                # Use CPID from DataFrame (authoritative)
                                cpid_value = None
                                try:
                                    if 'CPID' in selected_record.index and pd.notna(selected_record['CPID']):
                                        cpid_value = str(selected_record['CPID'])
                                    elif 'code' in selected_record.index and pd.notna(selected_record['code']):
                                        cpid_value = str(selected_record['code'])
                                except Exception:
                                    cpid_value = None

                                letter_id = st.session_state.letter_db.add_letter(
                                    prisoner_idx=row_idx,
                                    prisoner_record=selected_record,
                                    ocr_data=ocr_data,
                                    envelope_image_path=image_path_to_save,
                                    prisoner_code=cpid_value
                                )
                                st.info(f"📋 Letter #{letter_id} saved to database")
                                st.session_state.saved_letters[image_path_to_save] = letter_id
                    except Exception as autosave_err:
                        st.warning(f"Could not auto-save letter to DB: {autosave_err}")

                # Show actions if a prisoner is selected
                if st.session_state.show_actions and st.session_state.selected_prisoner_idx is not None:
                    row_idx = st.session_state.selected_prisoner_idx

                    # Display selected prisoner details
                    selected_record = st.session_state.df.iloc[row_idx]
                    st.subheader("Selected Prisoner Details:")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Name:** {selected_record['fName']} {selected_record['lName']}")
                        st.write(f"**CDCR #:** {selected_record['CDCRno']}")
                    with col2:
                        st.write(f"**Housing:** {selected_record['housing']}")

                    # Action buttons organized in columns
                    st.subheader("Available Actions:")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("📝 Update Letter Exchange", type="primary", use_container_width=True, key="update_exchange"):
                            # Handle NaN values in letter exchange
                            current_exchange = st.session_state.df.iloc[row_idx]['letter exchange (received only)']
                            if pd.isna(current_exchange) or current_exchange == "":
                                current_exchange = ""
                            else:
                                current_exchange = str(current_exchange)

                            new_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: OCR Document processed - {os.path.basename(image_path) if 'image_path' in locals() else 'Document'}"
                            if current_exchange.strip():
                                new_exchange = f"{current_exchange}\n---\n{new_entry}"
                            else:
                                new_exchange = new_entry

                            st.session_state.df.at[row_idx, 'letter exchange (received only)'] = new_exchange
                            
                            # Add to letter database if available
                            if LETTER_DB_AVAILABLE and 'letter_db' in st.session_state:
                                try:
                                    ocr_data = {
                                        'full_text': extracted_text,
                                        'return_address': st.session_state.get('return_address', '')
                                    }
                                    # Use a default image path if webcam wasn't used
                                    image_path_to_save = image_path if 'image_path' in locals() else 'uploaded_file'
                                    
                                    # Use CPID from the selected DataFrame row (authoritative, no recompute)
                                    cpid_value = None
                                    try:
                                        if 'CPID' in selected_record.index and pd.notna(selected_record['CPID']):
                                            cpid_value = str(selected_record['CPID'])
                                        elif 'code' in selected_record.index and pd.notna(selected_record['code']):
                                            cpid_value = str(selected_record['code'])
                                    except Exception:
                                        cpid_value = None
                                    
                                    letter_id = st.session_state.letter_db.add_letter(
                                        prisoner_idx=row_idx,
                                        prisoner_record=selected_record,
                                        ocr_data=ocr_data,
                                        envelope_image_path=image_path_to_save,
                                        prisoner_code=cpid_value
                                    )
                                    st.success(f"📋 Letter #{letter_id} added to database successfully!")
                                    
                                    # Debug: Show database status
                                    try:
                                        letter_count = len(st.session_state.letter_db.get_all_letters())
                                        st.info(f"📊 Database now contains {letter_count} letters")
                                    except Exception as count_error:
                                        st.warning(f"Could not count letters: {count_error}")
                                        
                                except Exception as db_error:
                                    st.error(f"❌ Could not save to letter database: {db_error}")
                                    import traceback
                                    st.code(traceback.format_exc())
                            else:
                                st.warning("⚠️ Letter database not available - letter not saved to database")
                                if not LETTER_DB_AVAILABLE:
                                    st.info("Database module not imported")
                                if 'letter_db' not in st.session_state:
                                    st.info("Database not initialized in session state")
                            
                            st.success("✅ Letter exchange updated successfully!")
                            st.balloons()

                        # Dedicated save to DB button (so a letter is recorded even if not updating the exchange)
                        if st.button("💾 Save Letter to Database", type="secondary", use_container_width=True, key="save_letter_db"):
                            try:
                                # Prepare data for DB
                                image_path_to_save = image_path if 'image_path' in locals() else 'uploaded_file'
                                ocr_data = {
                                    'full_text': extracted_text,
                                    'return_address': st.session_state.get('return_address', '')
                                }
                                # Use CPID from the selected DataFrame row (authoritative)
                                cpid_value = None
                                try:
                                    if 'CPID' in selected_record.index and pd.notna(selected_record['CPID']):
                                        cpid_value = str(selected_record['CPID'])
                                    elif 'code' in selected_record.index and pd.notna(selected_record['code']):
                                        cpid_value = str(selected_record['code'])
                                except Exception:
                                    cpid_value = None

                                # Save to DB
                                letter_id = st.session_state.letter_db.add_letter(
                                    prisoner_idx=row_idx,
                                    prisoner_record=selected_record,
                                    ocr_data=ocr_data,
                                    envelope_image_path=image_path_to_save,
                                    prisoner_code=cpid_value
                                )
                                st.success(f"📋 Letter #{letter_id} saved to database")
                                # Track in session to avoid duplicates
                                if 'saved_letters' in st.session_state:
                                    st.session_state.saved_letters[image_path_to_save] = letter_id
                            except Exception as e:
                                st.error(f"❌ Failed to save letter to DB: {e}")

                        if st.button("📝 Edit Prisoner Record", type="secondary", use_container_width=True, key="edit_record"):
                            st.session_state.edit_mode = True
                            st.rerun()

                    # Show edit form if in edit mode
                    if st.session_state.edit_mode:
                        st.subheader("Edit Complete Prisoner Record:")
                        
                        # Use form to prevent page reloads on field changes
                        with st.form(key="edit_prisoner_form"):
                            edited_record = {}
                            col1, col2 = st.columns(2)

                            columns = list(selected_record.index)
                            mid_point = len(columns) // 2

                            with col1:
                                st.markdown("**Basic Information:**")
                                for i, col in enumerate(columns[:mid_point]):
                                    current_value = selected_record[col]
                                    if pd.isna(current_value):
                                        current_value = ""

                                    # Handle different data types
                                    if col in ['CDCRno']:  # Numeric fields
                                        edited_record[col] = st.text_input(
                                            f"{col}:",
                                            value=str(current_value) if current_value != "" else "",
                                            key=f"form_edit_{col}_{row_idx}"
                                        )
                                    else:  # Text fields
                                        edited_record[col] = st.text_input(
                                            f"{col}:",
                                            value=str(current_value) if current_value != "" else "",
                                            key=f"form_edit_{col}_{row_idx}"
                                        )

                            with col2:
                                st.markdown("**Additional Information:**")
                                for i, col in enumerate(columns[mid_point:], mid_point):
                                    current_value = selected_record[col]
                                    if pd.isna(current_value):
                                        current_value = ""

                                    # Handle different data types
                                    if col in ['CDCRno']:  # Numeric fields
                                        edited_record[col] = st.text_input(
                                            f"{col}:",
                                            value=str(current_value) if current_value != "" else "",
                                            key=f"form_edit_{col}_{row_idx}"
                                        )
                                    else:  # Text fields
                                        edited_record[col] = st.text_area(
                                            f"{col}:",
                                            value=str(current_value) if current_value != "" else "",
                                            height=60 if len(str(current_value)) > 50 else 40,
                                            key=f"form_edit_{col}_{row_idx}"
                                        )

                            # Form buttons
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                save_clicked = st.form_submit_button("💾 Save Record Changes", type="primary", use_container_width=True)
                            with col_cancel:
                                cancel_clicked = st.form_submit_button("❌ Cancel Edit", type="secondary", use_container_width=True)

                            if save_clicked:
                                try:
                                    # Update the DataFrame with edited values
                                    for col, new_value in edited_record.items():
                                        if col in ['CDCRno'] and new_value.strip():
                                            # Try to convert to number for numeric fields
                                            try:
                                                st.session_state.df.at[row_idx, col] = int(new_value.strip())
                                            except ValueError:
                                                st.session_state.df.at[row_idx, col] = new_value.strip()
                                        else:
                                            # Handle empty strings as NaN for consistency
                                            if new_value.strip() == "":
                                                st.session_state.df.at[row_idx, col] = pd.NA
                                            else:
                                                st.session_state.df.at[row_idx, col] = new_value.strip()

                                    st.success("✅ Prisoner record updated successfully!")
                                    st.balloons()
                                    st.session_state.edit_mode = False
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"❌ Failed to save changes: {str(e)}")

                            if cancel_clicked:
                                st.session_state.edit_mode = False
                                st.rerun()

                    with col2:
                        if st.button("🏷️ Add to Envelope Queue", type="secondary", use_container_width=True, key="generate_label"):
                            # Create envelope entry
                            envelope_entry = {
                                'prisoner_idx': row_idx,
                                'name': f"{selected_record['fName']} {selected_record['lName']}",
                                'cdcr_no': selected_record['CDCRno'],
                                'housing': selected_record['housing'],
                                'address': selected_record.get('address', ''),
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                'source': 'OCR Processing'
                            }
                            
                            # Check if already in queue
                            already_queued = any(
                                entry['prisoner_idx'] == row_idx 
                                for entry in st.session_state.envelope_queue
                            )
                            
                            if not already_queued:
                                st.session_state.envelope_queue.append(envelope_entry)
                                st.success(f"✅ Added {envelope_entry['name']} to envelope queue!")
                                st.balloons()
                            else:
                                st.warning(f"⚠️ {envelope_entry['name']} is already in the envelope queue")

                    # Add Processing Note section (outside of any form)
                    st.markdown("---")
                    st.subheader("📝 Add Processing Note")
                    if st.button("📝 Add Processing Note", type="secondary", use_container_width=True, key="add_note"):
                        st.session_state.show_note_form = True
                        st.rerun()
                    
                    if st.session_state.get('show_note_form', False):
                        note_text = st.text_area("Enter processing note:", height=100,
                                               placeholder="Enter any notes about this document processing...", key="note_text")
                        col_save_note, col_cancel_note = st.columns(2)
                        with col_save_note:
                            if st.button("💾 Save Note", type="primary", key="save_note"):
                                if note_text.strip():
                                    # Add note to letter exchange or create a notes field
                                    current_notes = st.session_state.df.iloc[row_idx].get('processing_notes', '')
                                    if pd.isna(current_notes):
                                        current_notes = ""

                                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                                    new_note = f"{timestamp}: {note_text.strip()}"
                                    if current_notes.strip():
                                        updated_notes = f"{current_notes}\n---\n{new_note}"
                                    else:
                                        updated_notes = new_note

                                    # Add processing_notes column if it doesn't exist
                                    if 'processing_notes' not in st.session_state.df.columns:
                                        st.session_state.df['processing_notes'] = ""

                                    st.session_state.df.at[row_idx, 'processing_notes'] = updated_notes
                                    st.success("✅ Processing note added!")
                                    st.balloons()
                                    st.session_state.show_note_form = False
                                    st.rerun()
                                else:
                                    st.warning("Please enter a note before saving.")
                        with col_cancel_note:
                            if st.button("❌ Cancel Note", type="secondary", key="cancel_note"):
                                st.session_state.show_note_form = False
                                st.rerun()

                    # Clear selection button
                    if st.button("🔄 Clear Selection", type="secondary", key="clear_selection"):
                        st.session_state.selected_prisoner_idx = None
                        st.session_state.show_actions = False
                        st.session_state.show_note_form = False
                        # Force a rerun to update the UI
                        st.rerun()
            else:
                st.warning("No database matches found")

    # Save to Excel functionality (available when data is loaded)
    if not st.session_state.df.empty:
        st.markdown("---")  # Separator
        st.subheader("💾 Save Changes to Excel")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Generate default filename with today's date (Pacific Time)
            today = datetime.now()
            default_filename = f"prisoner_{today.strftime('%d%b%Y')}.xlsx"

            save_filename = st.text_input(
                "Excel filename:",
                value=default_filename,
                help="Enter the filename for the updated Excel file"
            )

        with col2:
            if st.button("💾 Save to Excel", type="primary", use_container_width=True):
                try:
                    # Save the DataFrame to Excel
                    output_path = os.path.join(project_root, save_filename)
                    st.session_state.df.to_excel(output_path, index=False)

                    st.success(f"✅ Excel file saved successfully!")
                    st.info(f"📁 File saved to: `{output_path}`")

                    # Show file size and record count
                    file_size = os.path.getsize(output_path)
                    record_count = len(st.session_state.df)
                    st.info(f"📊 Saved {record_count} records ({file_size:,} bytes)")

                except Exception as e:
                    st.error(f"❌ Failed to save Excel file: {str(e)}")
                    st.info("💡 Check file permissions and try a different filename")

render_ocr_processing()
