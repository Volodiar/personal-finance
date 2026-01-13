"""
auth.py - Google OAuth authentication using popup window.

Opens OAuth in a popup window, then redirects back to the app.
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
    Uses Google OAuth with popup window.
    """
    config = get_oauth_config()
    
    # Check for OAuth callback (code in URL)
    query_params = st.query_params
    code = query_params.get("code")
    
    if code and not st.session_state.get("authenticated"):
        # Exchange code for token
        with st.spinner("Signing you in..."):
            token_data = exchange_code_for_token(code, config)
            
            if "error" in token_data:
                st.error(f"Authentication failed: {token_data.get('error_description', token_data.get('error'))}")
                st.query_params.clear()
                return False
            
            access_token = token_data.get("access_token")
            if access_token:
                user_info = get_user_info(access_token)
                
                if "error" in user_info:
                    st.error(f"Could not get user info")
                    st.query_params.clear()
                    return False
                
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
        st.error(f"Sign in was cancelled or failed")
        st.query_params.clear()
    
    # Show login screen
    if config.get("client_id"):
        return show_oauth_login(config)
    else:
        st.error("OAuth not configured. Please add google_oauth to secrets.")
        return False


def show_oauth_login(config: Dict) -> bool:
    """Show Google OAuth login screen with popup."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>💰 Personal Finance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7); margin-bottom: 2rem;'>Smart Financial Tracking & Insights</p>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center;'>Welcome!</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7);'>Sign in with your Google account to access your financial data.</p>", unsafe_allow_html=True)
        
        # Generate auth URL
        auth_url = get_authorization_url(config)
        
        # Login button that opens popup window
        st.markdown(
            f"""
            <div style='text-align: center; margin: 2rem 0;'>
                <button onclick="openGoogleAuth()" style="
                    display: inline-block;
                    padding: 14px 28px;
                    background: #4285f4;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: 500;
                    font-size: 16px;
                    cursor: pointer;
                    box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
                    transition: all 0.2s;
                " onmouseover="this.style.background='#3367d6'" onmouseout="this.style.background='#4285f4'">
                    <span style="margin-right: 8px;">🔐</span> Sign in with Google
                </button>
            </div>
            <script>
                function openGoogleAuth() {{
                    // Open popup
                    var width = 500;
                    var height = 600;
                    var left = (screen.width - width) / 2;
                    var top = (screen.height - height) / 2;
                    var popup = window.open(
                        '{auth_url}',
                        'Google Sign In',
                        'width=' + width + ',height=' + height + ',left=' + left + ',top=' + top + ',scrollbars=yes'
                    );
                    
                    // Check if popup was blocked
                    if (!popup || popup.closed || typeof popup.closed == 'undefined') {{
                        // Popup blocked, navigate directly
                        window.top.location.href = '{auth_url}';
                    }}
                }}
            </script>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 2rem;'>Your data is private and secure.</p>", unsafe_allow_html=True)
    
    return False


def logout():
    """Log out the current user."""
    keys_to_clear = [
        "authenticated", "user_email", "user_name", "user_folder",
        "user_picture", "account_hash", "account_data_users"
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
