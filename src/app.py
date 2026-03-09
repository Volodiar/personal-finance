"""
app.py - Main Streamlit application for Personal Finance.
Refactored to be modular and cleaner.
"""

import streamlit as st

# App configuration must be first Streamlit command
st.set_page_config(
    page_title="Personal Finance",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import local modules
from storage import ensure_directories
from auth import check_password, get_current_user
from accounts import get_or_create_account
from sheets_storage import is_cloud_mode

# UI Modules
from ui.styles import apply_custom_styles
from ui.session import init_session_state
from ui.components import render_header_controls
from ui.home import render_home_screen, render_user_home
from ui.upload import render_upload_screen, render_save_success_screen
from ui.analytics.main import render_analytics_screen

def main():
    """Main application entry point."""
    # Apply styles first (for login page too)
    apply_custom_styles()
    
    # Check authentication - show login if not authenticated
    if not check_password():
        return
    
    # Auto-create/get user from OAuth email
    user_email = st.session_state.get("user_email", "")
    
    # Multi-tenant: Get or create account for this email
    if user_email and is_cloud_mode():
        account = get_or_create_account(user_email)
        if account:
            st.session_state.account_hash = account.get("hash", "")
            st.session_state.account_data_users = account.get("data_users", [])
    
    # Initialize after auth
    ensure_directories()
    init_session_state()
    
    # Render theme toggle and logout in header
    render_header_controls()
    
    # Route to appropriate screen
    current_screen = st.session_state.current_screen
    
    if current_screen == 'home':
        render_home_screen()
    elif current_screen == 'user_home':
        # This state might not be used if we go directly to analytics, 
        # but let's keep it for compatibility or future use.
        user = st.session_state.selected_user
        if user:
            render_user_home(user)
        else:
            st.session_state.current_screen = 'home'
            st.rerun()
    elif current_screen == 'upload':
        render_upload_screen()
    elif current_screen == 'success':
        render_save_success_screen()
    elif current_screen == 'analytics':
        render_analytics_screen()
    elif current_screen == 'joint_analytics':
        # This is now handled inside analytics screen tabs usually, 
        # but if explicit route exists:
        from ui.analytics.main import render_joint_analytics
        from services.factory import get_data_provider
        provider = get_data_provider()
        render_joint_analytics(provider.get_users())
    else:
        st.session_state.current_screen = 'home'
        st.rerun()

if __name__ == "__main__":
    main()
