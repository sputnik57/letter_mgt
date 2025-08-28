import streamlit as st

def caesar_code(first: str, last: str, no: str, s: int = 1) -> str:
    """
    Simple Caesar cipher that shifts characters in the combined string.

    Args:
        first (str): First name
        last (str): Last name
        no (str): ID or number
        s (int): Shift value (default is 1)

    Returns:
        str: Encoded string
    """
    combined = f"{first}{last}{no}"
    shifted = ''.join(chr((ord(c) + s) % 256) for c in combined)
    return shifted


def render_code_generator():
    """
    Streamlit UI component to generate and display a Caesar-coded string.
    """
    st.markdown('<h2 class="section-header">🔐 Generate Security Code</h2>', unsafe_allow_html=True)

    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    no = st.text_input("ID Number")
    shift = st.slider("Shift Amount", min_value=1, max_value=25, value=1)

    if st.button("Generate Code"):
        if first and last and no:
            code = caesar_code(first, last, no, shift)
            st.success(f"Generated Code: `{code}`")
        else:
            st.warning("Please fill out all fields.")