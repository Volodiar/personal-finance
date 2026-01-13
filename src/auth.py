"""
auth.py - Google OAuth authentication using manual flow.

This implementation uses direct OAuth calls for better debugging.
"""

import streamlit as st
import hashlib
import requests
from urllib.parse import urlencode
from typing import Dict


def email_to_user_folder(email: str) -> str:
    """Convert email to a safe folder/worksheet name."""
    if not email:
        return "anonymous"
    
    username = email.split("@")[0]
    safe_name = username.replace(".", "_").replace("-", "_").lower()
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    
    return safe_name or "user"


def get_oauth_config() -> Dict:
    """Get OAuth configuration from secrets."""
    try:
        oauth = st.secrets.get("google_oauth", {})
        return {
            "client_id": oauth.get("client_id", ""),
            "client_secret": oauth.get("client_secret", ""),
            "redirect_uri": oauth.get("redirect_uri", "http://localhost:8501"),
        }
    except:
        return {}


def get_authorization_url(config: Dict) -> str:
    """Generate Google OAuth authorization URL."""
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_code_for_token(code: str, config: Dict) -> Dict:
    """Exchange authorization code for access token."""
    try:
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "redirect_uri": config["redirect_uri"],
                "grant_type": "authorization_code",
            },
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def get_user_info(access_token: str) -> Dict:
    """Get user info from Google."""
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def check_password() -> bool:
    """
    Main authentication entry point.
    Uses Google OAuth or password fallback.
    """
    config = get_oauth_config()
    
    # Check for OAuth callback (code in URL)
    query_params = st.query_params
    code = query_params.get("code")
    
    if code and not st.session_state.get("authenticated"):
        # Exchange code for token
        with st.spinner("Authenticating..."):
            token_data = exchange_code_for_token(code, config)
            
            if "error" in token_data:
                st.error(f"Token error: {token_data.get('error_description', token_data.get('error'))}")
                st.query_params.clear()
                return check_password_fallback()
            
            access_token = token_data.get("access_token")
            if access_token:
                user_info = get_user_info(access_token)
                
                if "error" in user_info:
                    st.error(f"User info error: {user_info}")
                    st.query_params.clear()
                    return check_password_fallback()
                
                # Set session state
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = user_info.get("email", "")
                st.session_state["user_name"] = user_info.get("name", "User")
                st.session_state["user_folder"] = email_to_user_folder(user_info.get("email", ""))
                st.session_state["user_picture"] = user_info.get("picture", "")
                
                # Clear URL params and rerun
                st.query_params.clear()
                st.rerun()
    
    # Check if already authenticated
    if st.session_state.get("authenticated"):
        return True
    
    # Check for OAuth error
    error = query_params.get("error")
    if error:
        st.error(f"OAuth error: {error} - {query_params.get('error_description', '')}")
        st.query_params.clear()
    
    # Show login screen
    if config.get("client_id"):
        return show_oauth_login(config)
    else:
        return check_password_fallback()


def show_oauth_login(config: Dict) -> bool:
    """Show Google OAuth login screen."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>💰 Personal Finance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7); margin-bottom: 2rem;'>Smart Financial Tracking & Insights</p>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center;'>Welcome!</h3>", unsafe_allow_html=True)
        
        # Generate auth URL
        auth_url = get_authorization_url(config)
        
        # Debug info (expandable)
        with st.expander("🔧 Debug Info"):
            st.write("**Client ID:**", config["client_id"][:20] + "...")
            st.write("**Redirect URI:**", config["redirect_uri"])
            st.code(auth_url[:100] + "...", language=None)
        
        # Login button as a link
        st.markdown(
            f"""
            <div style='text-align: center; margin: 2rem 0;'>
                <a href="{auth_url}" target="_self" style="
                    display: inline-block;
                    padding: 12px 24px;
                    background: #4285f4;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: 500;
                    font-size: 16px;
                ">
                    🔐 Sign in with Google
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem;'>Your data is private and secure.</p>", unsafe_allow_html=True)
        
        # Fallback option
        st.markdown("---")
        if st.button("Use password login instead", use_container_width=True):
            st.session_state["use_password_login"] = True
            st.rerun()
    
    if st.session_state.get("use_password_login"):
        return check_password_fallback()
    
    return False


def check_password_fallback() -> bool:
    """Fallback to password authentication."""
    
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
            st.session_state["user_name"] = email.split("@")[0].replace(".", " ").title()
            st.session_state["user_folder"] = email_to_user_folder(email)
            st.session_state.pop("password_input", None)
            st.session_state.pop("email_input", None)
        else:
            st.session_state["login_error"] = True
    
    if st.session_state.get("authenticated"):
        return True
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>💰 Personal Finance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7);'>Enter your credentials</p>", unsafe_allow_html=True)
        
        st.text_input("📧 Email", key="email_input", placeholder="your@email.com")
        st.text_input("🔒 Password", type="password", key="password_input")
        
        if st.button("🔓 Login", use_container_width=True):
            password_entered()
            if st.session_state.get("authenticated"):
                st.rerun()
        
        if st.session_state.get("login_error"):
            st.error("❌ Incorrect password")
        
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem;'>Default: finance123</p>", unsafe_allow_html=True)
    
    return False


def logout():
    """Log out the current user."""
    keys_to_clear = [
        "authenticated", "user_email", "user_name", "user_folder",
        "user_picture", "account_hash", "account_data_users",
        "use_password_login", "login_error"
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
    
    st.rerun()


def get_current_user() -> Dict:
    """Get current authenticated user info."""
    return {
        "email": st.session_state.get("user_email", ""),
        "name": st.session_state.get("user_name", "User"),
        "folder": st.session_state.get("user_folder", "default"),
        "picture": st.session_state.get("user_picture", ""),
    }
