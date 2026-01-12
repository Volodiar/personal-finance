"""
auth.py - Simple password authentication for Streamlit Cloud.

Provides a login screen that protects the app with a password.
Password is stored securely in Streamlit secrets.
"""

import streamlit as st
import hashlib


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_password() -> bool:
    """
    Returns True if the user has entered the correct password.
    Shows a login form if not authenticated.
    """
    
    def password_entered():
        """Check if entered password is correct."""
        entered = st.session_state.get("password_input", "")
        
        # Get password from secrets or use default for local dev
        try:
            correct_hash = st.secrets.get("password_hash", "")
            if not correct_hash:
                # Fallback for local development (password: "finance123")
                correct_hash = hash_password("finance123")
        except Exception:
            # Local development without secrets
            correct_hash = hash_password("finance123")
        
        if hash_password(entered) == correct_hash:
            st.session_state["authenticated"] = True
            del st.session_state["password_input"]  # Don't store password
        else:
            st.session_state["authenticated"] = False
    
    # Check if already authenticated
    if st.session_state.get("authenticated", False):
        return True
    
    # Show login form
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 2rem;
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>💰 Personal Finance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7);'>Please enter your password to continue</p>", unsafe_allow_html=True)
        
        st.text_input(
            "Password",
            type="password",
            key="password_input",
            on_change=password_entered,
            placeholder="Enter password..."
        )
        
        if st.button("🔓 Login", use_container_width=True):
            password_entered()
        
        if "authenticated" in st.session_state and not st.session_state["authenticated"]:
            st.error("❌ Incorrect password")
        
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 2rem;'>Default password for testing: finance123</p>", unsafe_allow_html=True)
    
    return False


def logout():
    """Log out the current user."""
    st.session_state["authenticated"] = False
    st.rerun()
