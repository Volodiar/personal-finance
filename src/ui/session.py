import streamlit as st

def init_session_state():
    """Initialize session state variables."""
    if 'current_screen' not in st.session_state:
        st.session_state.current_screen = 'home'
    if 'selected_user' not in st.session_state:
        st.session_state.selected_user = None
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'original_categories' not in st.session_state:
        st.session_state.original_categories = {}
    if 'data_saved' not in st.session_state:
        st.session_state.data_saved = False
    if 'save_result' not in st.session_state:
        st.session_state.save_result = None
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'  # Default theme
    if 'learned_mappings' not in st.session_state:
        st.session_state.learned_mappings = {}
