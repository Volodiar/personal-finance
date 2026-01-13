"""
auth.py - Authentication for Streamlit Cloud.

Provides email-based login with password authentication.
Google OAuth temporarily disabled due to configuration issues.
"""

import streamlit as st
import hashlib
from typing import Dict


def hash_password(password: str) -> str:
    """Hash a password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def email_to_user_folder(email: str) -> str:
    """Convert email to a safe folder/worksheet name."""
    if not email:
        return "anonymous"
    
    username = email.split("@")[0]
    safe_name = username.replace(".", "_").replace("-", "_").lower()
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    
    return safe_name or "user"


def check_password() -> bool:
    """
    Email-based password authentication.
    User enters their email and a shared password.
    """
    
    def do_login():
        email = st.session_state.get("login_email", "").strip()
        entered_password = st.session_state.get("login_password", "")
        
        if not email:
            st.session_state["login_error"] = "Please enter your email"
            return
        
        if "@" not in email:
            st.session_state["login_error"] = "Please enter a valid email"
            return
        
        # Check password
        try:
            correct_hash = st.secrets.get("password_hash", "")
            if not correct_hash:
                correct_hash = hash_password("finance123")
        except Exception:
            correct_hash = hash_password("finance123")
        
        if hash_password(entered_password) == correct_hash:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email
            st.session_state["user_name"] = email.split("@")[0].replace(".", " ").title()
            st.session_state["user_folder"] = email_to_user_folder(email)
            st.session_state.pop("login_error", None)
            st.session_state.pop("login_email", None)
            st.session_state.pop("login_password", None)
        else:
            st.session_state["login_error"] = "Incorrect password"
    
    # Already authenticated
    if st.session_state.get("authenticated", False):
        return True
    
    # Show login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>💰 Personal Finance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7); margin-bottom: 2rem;'>Smart Financial Tracking & Insights</p>", unsafe_allow_html=True)
        
        st.markdown("<div style='padding: 1rem;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Sign In</h3>", unsafe_allow_html=True)
        
        st.text_input("📧 Email", key="login_email", placeholder="your.email@gmail.com")
        st.text_input("🔒 Password", type="password", key="login_password")
        
        if st.button("🔓 Login", use_container_width=True):
            do_login()
            if st.session_state.get("authenticated"):
                st.rerun()
        
        # Show error if any
        if st.session_state.get("login_error"):
            st.error(st.session_state["login_error"])
        
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 1rem;'>Default password: finance123</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    return False


def logout():
    """Log out the current user."""
    keys_to_clear = [
        "authenticated", "user_email", "user_name", "user_folder",
        "account_hash", "account_data_users", "login_error"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()


def get_current_user() -> Dict:
    """Get current authenticated user info."""
    return {
        "email": st.session_state.get("user_email", ""),
        "name": st.session_state.get("user_name", "User"),
        "folder": st.session_state.get("user_folder", "default"),
    }
