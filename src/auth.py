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
    """Show Google OAuth login screen - premium fintech design."""
    auth_url = get_authorization_url(config)

    st.markdown("""
    <style>
    /* Hide Streamlit default header/footer on login */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # Center the card using columns
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 3rem 2.5rem;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            font-family: 'Inter', sans-serif;
            margin-top: 3rem;
        ">
            <div style="font-size: 3.5rem; margin-bottom: 1rem;">💰</div>
            <div style="
                font-size: 2rem;
                font-weight: 800;
                background: linear-gradient(135deg, #4ECDC4, #FF6B9D);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 0.25rem;
            ">FinanceApp</div>
            <div style="color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-bottom: 2.5rem;">
                Smart Financial Tracking &amp; Insights
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.75rem; text-align: left; margin-bottom: 2rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem; color: rgba(255,255,255,0.65); font-size: 0.9rem;">
                    <span style="font-size: 1.1rem; width: 1.5rem; text-align: center;">📊</span>
                    <span>Track expenses across multiple profiles</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.75rem; color: rgba(255,255,255,0.65); font-size: 0.9rem;">
                    <span style="font-size: 1.1rem; width: 1.5rem; text-align: center;">🔮</span>
                    <span>AI-powered spending insights &amp; predictions</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.75rem; color: rgba(255,255,255,0.65); font-size: 0.9rem;">
                    <span style="font-size: 1.1rem; width: 1.5rem; text-align: center;">🎯</span>
                    <span>Budget management &amp; savings goals</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.75rem; color: rgba(255,255,255,0.65); font-size: 0.9rem;">
                    <span style="font-size: 1.1rem; width: 1.5rem; text-align: center;">🔒</span>
                    <span>Your data, private and secure</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.link_button("Sign in with Google →", auth_url, use_container_width=True)
        st.markdown(
            "<div style='text-align: center; color: rgba(255,255,255,0.3); font-size: 0.78rem; margin-top: 0.75rem;'>"
            "By signing in, you agree to our privacy policy. We only access your email address."
            "</div>",
            unsafe_allow_html=True
        )

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
