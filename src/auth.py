"""
auth.py - Google OAuth authentication for Streamlit Cloud.

Provides Google Sign-In authentication with session persistence.
Users log in with their Google account, and their email is used
to isolate their data.
"""

import streamlit as st
import json
import tempfile
import os
from typing import Dict

# Try to import Google OAuth library
try:
    from streamlit_google_auth import Authenticate
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False


def email_to_user_folder(email: str) -> str:
    """Convert email to a safe folder/worksheet name."""
    if not email:
        return "anonymous"
    
    username = email.split("@")[0]
    safe_name = username.replace(".", "_").replace("-", "_").lower()
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    
    return safe_name or "user"


def create_credentials_file() -> str:
    """
    Create a temporary credentials file from Streamlit secrets.
    Returns the path to the file.
    """
    try:
        # Get OAuth config from secrets
        oauth_config = st.secrets.get("google_oauth", {})
        client_id = oauth_config.get("client_id", "")
        client_secret = oauth_config.get("client_secret", "")
        redirect_uri = oauth_config.get("redirect_uri", "http://localhost:8501")
        
        if not client_id or not client_secret:
            return None
        
        # Create credentials in the format Google OAuth expects
        credentials = {
            "web": {
                "client_id": client_id,
                "project_id": "personalfinance",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri],
                "javascript_origins": [redirect_uri.rstrip("/")]
            }
        }
        
        # Write to temp file
        fd, path = tempfile.mkstemp(suffix=".json", prefix="google_oauth_")
        with os.fdopen(fd, 'w') as f:
            json.dump(credentials, f)
        
        return path
    except Exception as e:
        st.error(f"Could not create credentials file: {e}")
        return None


def check_password() -> bool:
    """
    Main authentication entry point.
    Uses Google OAuth if available, falls back to password.
    """
    # Check if OAuth is available and configured
    oauth_config = st.secrets.get("google_oauth", {})
    
    if not GOOGLE_AUTH_AVAILABLE or not oauth_config.get("client_id"):
        return check_password_fallback()
    
    try:
        # Create credentials file from secrets
        creds_path = create_credentials_file()
        if not creds_path:
            return check_password_fallback()
        
        # Get configuration
        redirect_uri = oauth_config.get("redirect_uri", "http://localhost:8501")
        cookie_key = st.secrets.get("cookie_key", "personal_finance_secret")
        
        # Initialize authenticator
        authenticator = Authenticate(
            secret_credentials_path=creds_path,
            cookie_name="personal_finance_auth",
            cookie_key=cookie_key,
            redirect_uri=redirect_uri,
            cookie_expiry_days=30
        )
        
        # Check if returning from Google login
        authenticator.check_authentification()
        
        # If connected, set session state
        if st.session_state.get("connected", False):
            user_info = st.session_state.get("user_info", {})
            email = user_info.get("email", "")
            name = user_info.get("name", "User")
            
            st.session_state.user_email = email
            st.session_state.user_name = name
            st.session_state.user_folder = email_to_user_folder(email)
            
            # Cleanup temp file
            try:
                os.unlink(creds_path)
            except:
                pass
            
            return True
        
        # Show login screen
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<h1 style='text-align: center;'>💰 Personal Finance</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7); margin-bottom: 2rem;'>Smart Financial Tracking & Insights</p>", unsafe_allow_html=True)
            
            st.markdown("<h3 style='text-align: center;'>Welcome!</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7);'>Sign in with your Google account</p>", unsafe_allow_html=True)
            
            # Show the login button
            authenticator.login()
            
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 2rem;'>Your data is private and secure.</p>", unsafe_allow_html=True)
        
        # Cleanup temp file
        try:
            os.unlink(creds_path)
        except:
            pass
        
        return False
        
    except Exception as e:
        st.error(f"Authentication error: {e}")
        import traceback
        st.code(traceback.format_exc())
        return check_password_fallback()


def check_password_fallback() -> bool:
    """Fallback to password authentication."""
    import hashlib
    
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def password_entered():
        entered = st.session_state.get("password_input", "")
        email = st.session_state.get("email_input", "user@local")
        
        try:
            correct_hash = st.secrets.get("password_hash", "")
            if not correct_hash:
                correct_hash = hash_password("finance123")
        except:
            correct_hash = hash_password("finance123")
        
        if hash_password(entered) == correct_hash:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email
            st.session_state["user_name"] = email.split("@")[0].title()
            st.session_state["user_folder"] = email_to_user_folder(email)
            st.session_state.pop("password_input", None)
            st.session_state.pop("email_input", None)
        else:
            st.session_state["authenticated"] = False
    
    if st.session_state.get("authenticated", False):
        return True
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>💰 Personal Finance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7);'>Enter your credentials</p>", unsafe_allow_html=True)
        
        st.text_input("Email", key="email_input", placeholder="your@email.com")
        st.text_input("Password", type="password", key="password_input")
        
        if st.button("🔓 Login", use_container_width=True):
            password_entered()
            if st.session_state.get("authenticated"):
                st.rerun()
        
        if st.session_state.get("authenticated") == False:
            st.error("❌ Incorrect password")
        
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem;'>Default: finance123</p>", unsafe_allow_html=True)
    
    return False


def logout():
    """Log out the current user."""
    keys_to_clear = [
        "connected", "user_info", "authenticated",
        "user_email", "user_name", "user_folder",
        "account_hash", "account_data_users", "oauth_id"
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
