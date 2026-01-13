"""
auth.py - Google OAuth authentication for Streamlit Cloud.

Provides Google Sign-In authentication with session persistence.
Users log in with their Google account, and their email is used
to isolate their data.
"""

import streamlit as st
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
    
    # Take part before @ and clean it
    username = email.split("@")[0]
    # Replace dots and special chars with underscore
    safe_name = username.replace(".", "_").replace("-", "_").lower()
    # Remove any remaining special characters
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    
    return safe_name or "user"


def check_google_auth() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if user is authenticated via Google OAuth.
    
    Returns:
        Tuple of (is_authenticated, email, name)
    """
    if not GOOGLE_AUTH_AVAILABLE:
        return False, None, None
    
    config = get_oauth_config()
    if not config.get("client_id"):
        return False, None, None
    
    try:
        authenticator = Authenticate(
            secret_credentials_file=None,
            cookie_name="personal_finance_auth",
            cookie_key=st.secrets.get("cookie_key", "personal_finance_secret_key"),
            redirect_uri=config["redirect_uri"],
            cookie_expiry_days=30,  # Remember login for 30 days
        )
        
        authenticator.check_authentification()
        
        if st.session_state.get("connected", False):
            email = st.session_state.get("user_info", {}).get("email", "")
            name = st.session_state.get("user_info", {}).get("name", "User")
            return True, email, name
        
        return False, None, None
    except Exception as e:
        st.warning(f"OAuth error: {e}")
        return False, None, None


def render_google_login() -> bool:
    """
    Render Google login button and handle authentication.
    
    Returns:
        True if user is authenticated
    """
    config = get_oauth_config()
    
    # Check if OAuth is configured
    if not GOOGLE_AUTH_AVAILABLE or not config.get("client_id"):
        # Fall back to password auth
        return check_password_fallback()
    
    try:
        authenticator = Authenticate(
            secret_credentials_file=None,
            cookie_name="personal_finance_auth",
            cookie_key=st.secrets.get("cookie_key", "personal_finance_secret_key"),
            redirect_uri=config["redirect_uri"],
            cookie_expiry_days=30,
        )
        
        # Check existing authentication
        authenticator.check_authentification()
        
        if st.session_state.get("connected", False):
            # User is authenticated
            email = st.session_state.get("user_info", {}).get("email", "")
            name = st.session_state.get("user_info", {}).get("name", "User")
            
            # Set user folder in session
            st.session_state.user_email = email
            st.session_state.user_name = name
            st.session_state.user_folder = email_to_user_folder(email)
            
            return True
        
        # Show login screen
        st.markdown("""
        <style>
        .login-container {
            max-width: 450px;
            margin: 80px auto;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<h1 style='text-align: center;'>💰 Personal Finance</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7); margin-bottom: 2rem;'>Smart Financial Tracking & Insights</p>", unsafe_allow_html=True)
            
            st.markdown("<div class='glass-card' style='padding: 2rem; text-align: center;'>", unsafe_allow_html=True)
            st.markdown("<h3>Welcome!</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: rgba(255,255,255,0.7);'>Sign in with your Google account to access your financial data securely.</p>", unsafe_allow_html=True)
            
            # Google login button
            authenticator.login()
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 2rem;'>Your data is private and only accessible to you.</p>", unsafe_allow_html=True)
        
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
    # Clear all auth-related session state
    keys_to_clear = [
        "connected", "user_info", "authenticated",
        "user_email", "user_name", "user_folder"
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


def is_user_authorized_for_joint_view(email: str) -> bool:
    """
    Check if user is authorized to see joint view (all users' data).
    
    Configure authorized emails in Streamlit secrets:
    [authorized_users]
    joint_view = ["pablo@gmail.com", "masha@gmail.com"]
    """
    try:
        authorized = st.secrets.get("authorized_users", {}).get("joint_view", [])
        return email in authorized
    except Exception:
        # By default, no joint view for OAuth users
        return False
