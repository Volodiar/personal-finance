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
from typing import Optional, Dict, Tuple

# Try to import Google OAuth library
try:
    from streamlit_google_auth import Authenticate
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False


def get_oauth_config() -> Dict:
    """Get OAuth configuration from Streamlit secrets."""
    try:
        return {
            "client_id": st.secrets.get("google_oauth", {}).get("client_id", ""),
            "client_secret": st.secrets.get("google_oauth", {}).get("client_secret", ""),
            "redirect_uri": st.secrets.get("google_oauth", {}).get("redirect_uri", "http://localhost:8501"),
        }
    except Exception:
        return {}


def email_to_user_folder(email: str) -> str:
    """
    Convert email to a safe folder/worksheet name.
    
    Example: "pablo.parreno@gmail.com" -> "pablo_parreno"
    """
    if not email:
        return "anonymous"
    
    username = email.split("@")[0]
    safe_name = username.replace(".", "_").replace("-", "_").lower()
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    
    return safe_name or "user"


def create_credentials_file() -> Optional[str]:
    """
    Create a temporary credentials file from secrets.
    Returns the path to the file.
    """
    try:
        config = get_oauth_config()
        if not config.get("client_id"):
            return None
        
        credentials = {
            "web": {
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "redirect_uris": [config["redirect_uri"]],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        
        # Create temp file
        fd, path = tempfile.mkstemp(suffix=".json", prefix="oauth_")
        with os.fdopen(fd, 'w') as f:
            json.dump(credentials, f)
        
        return path
    except Exception as e:
        st.error(f"Could not create credentials file: {e}")
        return None


def render_google_login() -> bool:
    """
    Render Google login button and handle authentication.
    
    Returns:
        True if user is authenticated
    """
    config = get_oauth_config()
    
    # Check if OAuth is configured
    if not GOOGLE_AUTH_AVAILABLE or not config.get("client_id"):
        return check_password_fallback()
    
    try:
        # Create credentials file
        creds_path = create_credentials_file()
        if not creds_path:
            return check_password_fallback()
        
        cookie_key = st.secrets.get("cookie_key", "personal_finance_secret_key")
        
        authenticator = Authenticate(
            secret_credentials_path=creds_path,
            redirect_uri=config["redirect_uri"],
            cookie_name="personal_finance_auth",
            cookie_key=cookie_key,
            cookie_expiry_days=30,
        )
        
        # Check existing authentication
        authenticator.check_authentification()
        
        if st.session_state.get("connected", False):
            # User is authenticated
            email = st.session_state.get("user_info", {}).get("email", "")
            name = st.session_state.get("user_info", {}).get("name", "User")
            
            # Set user info in session
            st.session_state.user_email = email
            st.session_state.user_name = name
            st.session_state.user_folder = email_to_user_folder(email)
            
            # Clean up temp file
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
            
            st.markdown("<div style='padding: 2rem; text-align: center;'>", unsafe_allow_html=True)
            st.markdown("<h3>Welcome!</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: rgba(255,255,255,0.7);'>Sign in with your Google account to access your financial data securely.</p>", unsafe_allow_html=True)
            
            # Google login button
            authenticator.login()
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 2rem;'>Your data is private and only accessible to you.</p>", unsafe_allow_html=True)
        
        # Clean up temp file
        try:
            os.unlink(creds_path)
        except:
            pass
        
        return False
        
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return check_password_fallback()


def check_password_fallback() -> bool:
    """
    Fallback to password authentication when OAuth is not configured.
    Used for local development or when OAuth is not set up.
    """
    import hashlib
    
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def password_entered():
        entered = st.session_state.get("password_input", "")
        try:
            correct_hash = st.secrets.get("password_hash", "")
            if not correct_hash:
                correct_hash = hash_password("finance123")
        except Exception:
            correct_hash = hash_password("finance123")
        
        if hash_password(entered) == correct_hash:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = "local@user"
            st.session_state["user_name"] = "Local User"
            st.session_state["user_folder"] = "local"
            del st.session_state["password_input"]
        else:
            st.session_state["authenticated"] = False
    
    if st.session_state.get("authenticated", False):
        return True
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>💰 Personal Finance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7);'>Enter password to continue</p>", unsafe_allow_html=True)
        
        st.text_input("Password", type="password", key="password_input", on_change=password_entered)
        
        if st.button("🔓 Login", use_container_width=True):
            password_entered()
        
        if "authenticated" in st.session_state and not st.session_state["authenticated"]:
            st.error("❌ Incorrect password")
        
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 1rem;'>Default: finance123 (Google OAuth not configured)</p>", unsafe_allow_html=True)
    
    return False


def check_password() -> bool:
    """
    Main authentication entry point.
    Tries Google OAuth first, falls back to password.
    """
    return render_google_login()


def logout():
    """Log out the current user."""
    keys_to_clear = [
        "connected", "user_info", "authenticated",
        "user_email", "user_name", "user_folder",
        "account_hash", "account_data_users"
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
