"""
app.py - Main Streamlit application for Personal Finance.

A personal accounting app with glassmorphism UI featuring:
- Dynamic user management with emoji selection
- CSV upload with auto-categorization and smart merging
- Analytics dashboard with budgets, insights, and period views
- Monthly savings goal tracking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# App configuration must be first Streamlit command
st.set_page_config(
    page_title="Personal Finance",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import local modules after st.set_page_config
from categories import get_category_options, ALL_CATEGORIES
from data_processor import parse_bank_file, process_dataframe, get_month_year_from_data
from storage import (
    ensure_directories, load_learned_mappings, update_learned_mappings,
    add_transactions, load_user_data, load_all_data, 
    get_available_months, get_available_years
)
from analytics import (
    create_category_pie_chart, create_comparison_bar_chart,
    calculate_kpis, create_trend_chart, create_income_expense_trend,
    create_daily_chart_all, create_monthly_chart, create_annual_chart,
    create_category_breakdown_chart, create_category_trend, create_financial_summary_bar,
    get_daily_summary, get_monthly_summary, get_annual_summary, 
    get_category_summary, get_category_breakdown, filter_data_by_period
)
from budgets import (
    get_user_budgets, set_category_budget, remove_category_budget,
    get_user_goals, add_goal, update_goal_progress, delete_goal,
    calculate_budget_status, calculate_goal_progress, get_budget_alerts
)
from insights import (
    detect_recurring_transactions, get_monthly_fixed_costs,
    calculate_spending_velocity, detect_anomalies, get_prediction_insights,
    get_transaction_calendar
)
from user_manager import (
    load_users, add_user, delete_user, update_user, get_user_folder,
    get_user_count, should_show_joint_view, AVAILABLE_EMOJIS
)
from savings_goal import (
    load_savings_goal, save_savings_goal, get_monthly_target,
    calculate_savings_progress, get_category_variance
)
from auth import check_password, logout, get_current_user
from accounts import (
    get_or_create_account, get_data_users, add_data_user, delete_data_user,
    update_data_user, get_account_hash
)
from sheets_storage import (
    load_data_user_transactions, save_data_user_transactions,
    add_transactions as add_transactions_sheets, load_all_data_users_transactions,
    is_cloud_mode
)


# ============================================================================
# GLASSMORPHISM CSS STYLING
# ============================================================================

def apply_custom_styles():
    """Apply glassmorphism and modern styling with theme support."""
    # Get current theme from session state
    is_dark = st.session_state.get('theme', 'dark') == 'dark'
    
    # Theme-specific CSS variables
    if is_dark:
        theme_vars = """
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-tertiary: #0f3460;
            --bg-card: rgba(255, 255, 255, 0.05);
            --bg-card-hover: rgba(255, 255, 255, 0.1);
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.7);
            --text-muted: rgba(255, 255, 255, 0.5);
            --border-color: rgba(255, 255, 255, 0.1);
            --accent-primary: #4ECDC4;
            --accent-secondary: #44A08D;
            --accent-pink: #FF6B9D;
            --danger: #FF6B6B;
            --success: #2ECC71;
            --warning: #FFE66D;
            --shadow: rgba(0, 0, 0, 0.3);
        }
        """
    else:
        theme_vars = """
        :root {
            --bg-primary: #f5f7fa;
            --bg-secondary: #e8ecf1;
            --bg-tertiary: #dde3eb;
            --bg-card: rgba(255, 255, 255, 0.9);
            --bg-card-hover: rgba(255, 255, 255, 1);
            --text-primary: #1a1a2e;
            --text-secondary: rgba(26, 26, 46, 0.7);
            --text-muted: rgba(26, 26, 46, 0.5);
            --border-color: rgba(0, 0, 0, 0.1);
            --accent-primary: #3DBDB5;
            --accent-secondary: #2E8B7A;
            --accent-pink: #E85A8A;
            --danger: #E74C3C;
            --success: #27AE60;
            --warning: #F1C40F;
            --shadow: rgba(0, 0, 0, 0.1);
        }
        """
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    {theme_vars}
    
    /* Global styles */
    .stApp {{
        background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 50%, var(--bg-tertiary) 100%);
        font-family: 'Inter', sans-serif;
    }}
    
    /* Glassmorphism card */
    .glass-card {{
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid var(--border-color);
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px var(--shadow);
    }}
    
    /* Profile buttons */
    .profile-btn {{
        background: linear-gradient(135deg, rgba(255, 107, 157, 0.3) 0%, rgba(255, 107, 157, 0.1) 100%);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(255, 107, 157, 0.4);
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        color: var(--text-primary);
    }}
    
    .profile-btn:hover {{
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(255, 107, 157, 0.3);
        border-color: rgba(255, 107, 157, 0.8);
    }}
    
    .profile-btn.pablo {{
        background: linear-gradient(135deg, rgba(78, 205, 196, 0.3) 0%, rgba(78, 205, 196, 0.1) 100%);
        border-color: rgba(78, 205, 196, 0.4);
    }}
    
    .profile-btn.pablo:hover {{
        box-shadow: 0 15px 40px rgba(78, 205, 196, 0.3);
        border-color: rgba(78, 205, 196, 0.8);
    }}
    
    /* KPI cards */
    .kpi-card {{
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid var(--border-color);
    }}
    
    .kpi-value {{
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-primary);
        margin: 0.5rem 0;
    }}
    
    .kpi-label {{
        font-size: 0.9rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* Headers */
    h1 {{
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        text-align: center;
        margin-bottom: 2rem !important;
    }}
    
    h2, h3 {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}
    
    p, label, span {{
        color: var(--text-secondary);
    }}
    
    /* Theme toggle button */
    .theme-toggle {{
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1000;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 50%;
        width: 45px;
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1.3rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px var(--shadow);
    }}
    
    .theme-toggle:hover {{
        transform: scale(1.1);
        box-shadow: 0 6px 20px var(--shadow);
    }}
    
    /* Streamlit overrides */
    .stButton > button {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        min-height: 44px; /* Touch-friendly */
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(78, 205, 196, 0.4);
    }}
    
    .stDataFrame {{
        background: var(--bg-card);
        border-radius: 10px;
    }}
    
    /* File uploader */
    .stFileUploader {{
        background: var(--bg-card);
        border-radius: 15px;
        padding: 1rem;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: var(--bg-card);
        border-radius: 15px;
        padding: 0.5rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px;
        color: var(--text-primary);
        padding: 0.5rem 1rem;
        min-height: 44px; /* Touch-friendly */
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
    }}
    
    /* Success message styling */
    .success-box {{
        background: rgba(78, 205, 196, 0.15);
        border: 2px solid rgba(78, 205, 196, 0.5);
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }}
    
    .success-icon {{
        font-size: 3rem;
        margin-bottom: 1rem;
    }}
    
    /* Input fields */
    .stTextInput input, .stSelectbox select, .stDateInput input {{
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        min-height: 44px; /* Touch-friendly */
    }}
    
    /* Improved grid handling - prevent overflow */
    .stColumns > div {{
        min-width: 0;
    }}
    
    /* Desktop large screens */
    @media (min-width: 1200px) {{
        .glass-card {{
            padding: 2.5rem;
        }}
        
        .kpi-value {{
            font-size: 2.2rem;
        }}
    }}
    
    /* Tablet (768px - 1024px) */
    @media (min-width: 768px) and (max-width: 1024px) {{
        .glass-card {{
            padding: 1.5rem;
            margin: 0.75rem 0;
        }}
        
        .kpi-card {{
            padding: 1.2rem;
        }}
        
        .kpi-value {{
            font-size: 1.6rem;
        }}
        
        .kpi-label {{
            font-size: 0.8rem;
        }}
        
        .profile-btn {{
            padding: 2rem 1.5rem;
        }}
        
        h1 {{
            font-size: 1.75rem !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
        }}
    }}
    
    /* Mobile (max-width: 768px) */
    @media (max-width: 768px) {{
        .glass-card {{
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 15px;
        }}
        
        .kpi-card {{
            padding: 1rem;
            margin-bottom: 0.5rem;
        }}
        
        .kpi-value {{
            font-size: 1.4rem;
        }}
        
        .kpi-label {{
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }}
        
        .profile-btn {{
            padding: 1.5rem 1rem;
        }}
        
        h1 {{
            font-size: 1.5rem !important;
            margin-bottom: 1rem !important;
        }}
        
        h3 {{
            font-size: 1.1rem !important;
        }}
        
        /* Horizontal scrolling tabs on mobile */
        .stTabs [data-baseweb="tab-list"] {{
            overflow-x: auto;
            flex-wrap: nowrap;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none; /* Firefox */
            -ms-overflow-style: none; /* IE/Edge */
            padding-bottom: 5px;
        }}
        
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {{
            display: none; /* Chrome/Safari */
        }}
        
        .stTabs [data-baseweb="tab"] {{
            font-size: 0.8rem;
            padding: 0.4rem 0.8rem;
            white-space: nowrap;
            flex-shrink: 0;
        }}
        
        /* Stack columns on mobile */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap;
        }}
        
        [data-testid="stHorizontalBlock"] > div {{
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }}
    }}
    
    /* Small Mobile (max-width: 480px) */
    @media (max-width: 480px) {{
        .glass-card {{
            padding: 0.75rem;
            border-radius: 12px;
        }}
        
        .kpi-card {{
            padding: 0.75rem;
        }}
        
        .kpi-value {{
            font-size: 1.2rem;
        }}
        
        .kpi-label {{
            font-size: 0.7rem;
        }}
        
        h1 {{
            font-size: 1.25rem !important;
        }}
        
        h3 {{
            font-size: 1rem !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            font-size: 0.75rem;
            padding: 0.35rem 0.6rem;
        }}
        
        /* Ensure charts don't overflow */
        .js-plotly-plot {{
            max-width: 100% !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

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


def render_header_controls():
    """Render theme toggle and logout button in the header."""
    theme = st.session_state.get('theme', 'dark')
    theme_icon = "🌙" if theme == 'dark' else "☀️"
    
    # Use columns to position controls in top right
    cols = st.columns([9, 1, 1])
    
    with cols[1]:
        if st.button(theme_icon, key="theme_toggle", help="Toggle Dark/Light mode"):
            st.session_state.theme = 'light' if theme == 'dark' else 'dark'
            st.rerun()
    
    with cols[2]:
        if st.button("🚪", key="logout_btn", help="Logout"):
            logout()


def render_theme_toggle():
    """Legacy function - redirects to render_header_controls."""
    render_header_controls()


# ============================================================================
# SCREEN 1: HOME / LANDING PAGE
# ============================================================================

def render_home_screen():
    """Render the home/landing screen with data user management."""
    # App header
    user_email = st.session_state.get("user_email", "")
    user_name = st.session_state.get("user_name", "User")
    
    st.markdown("<h1>💰 Personal Finance</h1>", unsafe_allow_html=True)
    if user_email:
        st.markdown(f"<p style='text-align: center; color: rgba(255,255,255,0.7);'>Welcome, {user_name}!</p>", unsafe_allow_html=True)
    
    # Get account's data users (from session state, set in main())
    data_users = st.session_state.get("account_data_users", [])
    
    # Fallback to local users if not in cloud mode
    if not is_cloud_mode():
        data_users = [{"id": u["folder"], "name": u["name"], "emoji": u.get("emoji", "👤")} for u in load_users()]
    
    # Main content area
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        # Data User selection section
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>👥 Select Profile</h3>", unsafe_allow_html=True)
        
        if data_users:
            num_users = len(data_users)
            cols = st.columns(min(num_users + 1, 4))
            
            for i, du in enumerate(data_users):
                with cols[i % len(cols)]:
                    emoji = du.get('emoji', '👤')
                    name = du.get('name', du.get('id', 'User'))
                    data_user_id = du.get('id', name.lower())
                    
                    if st.button(f"{emoji} {name}", key=f"du_{data_user_id}", use_container_width=True):
                        st.session_state.selected_data_user_id = data_user_id
                        st.session_state.selected_data_user_name = name
                        st.session_state.current_screen = "user_home"
                        st.rerun()
            
            # Add data user button
            with cols[-1] if num_users < 4 else st.columns(4)[-1]:
                if st.button("➕ Add Profile", key="add_du_btn", use_container_width=True):
                    st.session_state.show_add_data_user = True
                    st.rerun()
        else:
            st.info("No profiles yet! Create your first profile to get started.")
            if st.button("➕ Create First Profile", use_container_width=True):
                st.session_state.show_add_data_user = True
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Add data user modal
        if st.session_state.get('show_add_data_user', False):
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<h4>➕ Add New Profile</h4>", unsafe_allow_html=True)
            
            new_name = st.text_input("Name", placeholder="Enter profile name", key="new_du_name")
            
            st.markdown("<p style='color: rgba(255,255,255,0.7);'>Select an emoji:</p>", unsafe_allow_html=True)
            
            emoji_cols = st.columns(8)
            selected_emoji = st.session_state.get('selected_emoji', '👤')
            
            for i, emoji in enumerate(AVAILABLE_EMOJIS[:24]):
                with emoji_cols[i % 8]:
                    if st.button(emoji, key=f"emoji_{i}", use_container_width=True):
                        st.session_state.selected_emoji = emoji
                        st.rerun()
            
            st.markdown(f"<p style='text-align: center; font-size: 2rem;'>Selected: {selected_emoji}</p>", unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Create Profile", use_container_width=True):
                    if new_name:
                        if is_cloud_mode() and user_email:
                            # Add to account in cloud
                            if add_data_user(user_email, new_name, selected_emoji):
                                st.session_state.show_add_data_user = False
                                st.session_state.selected_emoji = '👤'
                                # Refresh account data
                                account = get_or_create_account(user_email)
                                st.session_state.account_data_users = account.get("data_users", [])
                                st.success(f"Profile '{new_name}' created!")
                                st.rerun()
                            else:
                                st.error("Profile already exists!")
                        else:
                            # Local mode - use old system
                            if add_user(new_name, selected_emoji):
                                st.session_state.show_add_data_user = False
                                st.success(f"Profile '{new_name}' created!")
                                st.rerun()
                            else:
                                st.error("Profile already exists!")
                    else:
                        st.warning("Please enter a name")
            
            with col_b:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_add_data_user = False
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Quick actions
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>⚡ Quick Actions</h3>", unsafe_allow_html=True)
        
        show_joint = len(data_users) > 1
        action_cols = st.columns(2 if show_joint else 1)
        
        with action_cols[0]:
            if st.button("📊 View Analytics Dashboard", use_container_width=True):
                st.session_state.current_screen = "analytics"
                st.rerun()
        
        if show_joint:
            with action_cols[1]:
                if st.button("👥 Joint Analytics", use_container_width=True):
                    st.session_state.current_screen = "joint_analytics"
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)


def render_user_home(data_user_id: str):
    """Render home screen for a specific data user (profile)."""
    user_email = st.session_state.get("user_email", "")
    account_hash = st.session_state.get("account_hash", "")
    data_users = st.session_state.get("account_data_users", [])
    
    # Find the data user
    data_user = next((du for du in data_users if du.get('id') == data_user_id), None)
    
    # Fallback to local user system if not in cloud
    if not data_user and not is_cloud_mode():
        users = load_users()
        local_user = next((u for u in users if u['folder'] == data_user_id), None)
        if local_user:
            data_user = {"id": data_user_id, "name": local_user['name'], "emoji": local_user.get('emoji', '👤')}
    
    if not data_user:
        st.error("Profile not found!")
        if st.button("← Back to Home"):
            st.session_state.current_screen = "home"
            st.rerun()
        return
    
    user_name = data_user.get('name', data_user_id)
    user_emoji = data_user.get('emoji', '👤')
    
    # Header with back button
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← Back"):
            st.session_state.current_screen = "home"
            st.session_state.selected_data_user_id = None
            st.rerun()
    with col2:
        st.markdown(f"<h1>{user_emoji} {user_name}</h1>", unsafe_allow_html=True)
    with col3:
        if st.button("⚙️ Settings", key="user_settings"):
            st.session_state.show_user_settings = True
            st.rerun()
    
    # User settings modal
    if st.session_state.get('show_user_settings', False):
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4>⚙️ Profile Settings</h4>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            current_emoji_idx = AVAILABLE_EMOJIS.index(user_emoji) if user_emoji in AVAILABLE_EMOJIS else 0
            new_emoji = st.selectbox("Change Emoji", AVAILABLE_EMOJIS, index=current_emoji_idx)
            if st.button("Update Emoji", use_container_width=True):
                if is_cloud_mode() and user_email:
                    update_data_user(user_email, data_user_id, new_emoji=new_emoji)
                    account = get_or_create_account(user_email)
                    st.session_state.account_data_users = account.get("data_users", [])
                else:
                    update_user(user_name, new_emoji=new_emoji)
                st.success("Emoji updated!")
                st.session_state.show_user_settings = False
                st.rerun()
        
        with col_b:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Delete Profile", use_container_width=True):
                st.session_state.confirm_delete = True
        
        if st.session_state.get('confirm_delete', False):
            st.warning(f"⚠️ Are you sure you want to delete '{user_name}'? This will remove all their data!")
            col_y, col_n = st.columns(2)
            with col_y:
                if st.button("Yes, Delete", use_container_width=True):
                    if is_cloud_mode() and user_email:
                        delete_data_user(user_email, data_user_id)
                        account = get_or_create_account(user_email)
                        st.session_state.account_data_users = account.get("data_users", [])
                    else:
                        delete_user(user_name)
                    st.session_state.current_screen = "home"
                    st.session_state.selected_data_user_id = None
                    st.session_state.confirm_delete = False
                    st.session_state.show_user_settings = False
                    st.rerun()
            with col_n:
                if st.button("No, Cancel", use_container_width=True):
                    st.session_state.confirm_delete = False
                    st.rerun()
        
        if st.button("Close Settings", use_container_width=True):
            st.session_state.show_user_settings = False
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Main actions
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📤 Upload Data</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: rgba(255,255,255,0.7);'>Upload new bank statements</p>", unsafe_allow_html=True)
        if st.button("📂 Upload CSV", key="upload_btn", use_container_width=True):
            st.session_state.current_screen = "upload"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📊 Dashboard</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: rgba(255,255,255,0.7);'>View your financial analytics</p>", unsafe_allow_html=True)
        if st.button("📈 View Dashboard", key="dashboard_btn", use_container_width=True):
            st.session_state.current_screen = "analytics"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Quick stats preview - load from appropriate source
    if is_cloud_mode() and account_hash:
        data = load_data_user_transactions(account_hash, data_user_id)
    else:
        data = load_user_data(data_user_id)
    
    if not data.empty:
        kpis = calculate_kpis(data)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📈 Quick Stats</h3>", unsafe_allow_html=True)
        
        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            color = '#2ECC71' if kpis['balance'] >= 0 else '#FF6B6B'
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Balance</div><div class='kpi-value' style='color: {color};'>€{kpis['balance']:,.0f}</div></div>", unsafe_allow_html=True)
        with kpi_cols[1]:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Income</div><div class='kpi-value' style='color: #2ECC71;'>€{kpis['total_income']:,.0f}</div></div>", unsafe_allow_html=True)
        with kpi_cols[2]:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Expenses</div><div class='kpi-value' style='color: #FF6B6B;'>€{kpis['total_expenses']:,.0f}</div></div>", unsafe_allow_html=True)
        with kpi_cols[3]:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Transactions</div><div class='kpi-value'>{kpis['expense_count'] + kpis['income_count']}</div></div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# SCREEN 2: UPLOAD & VALIDATION
# ============================================================================

def render_upload_screen():
    """Render the upload and validation screen."""
    user = st.session_state.selected_user
    user_display = user.capitalize()
    
    # Header with back button
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("← Back"):
            st.session_state.current_screen = "profile_select"
            st.session_state.processed_data = None
            st.session_state.data_saved = False
            st.rerun()
    with col2:
        st.markdown(f"<h1>📤 Upload Expenses - {user_display}</h1>", unsafe_allow_html=True)
    
    # Check if we just saved data - show success screen
    if st.session_state.data_saved and st.session_state.save_result:
        render_save_success_screen()
        return
    
    # File uploader
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload your bank statement (CSV, Excel, or PDF)",
        type=['csv', 'xlsx', 'xls', 'pdf'],
        help="Supported formats: CSV, Excel, PDF (Trade Republic style)."
    )
    
    if uploaded_file is not None:
        try:
            # Parse and process the file
            raw_df = parse_bank_file(uploaded_file)
            learned_mappings = load_learned_mappings()
            processed_df = process_dataframe(raw_df, learned_mappings)
            
            # Store in session state
            st.session_state.processed_data = processed_df
            
            # Track original categories for learning
            st.session_state.original_categories = dict(
                zip(processed_df['Concepto'], processed_df['Category'].fillna(''))
            )
            
            # Show date range info
            if 'Date' in processed_df.columns:
                valid_dates = processed_df['Date'].dropna()
                if not valid_dates.empty:
                    min_date = valid_dates.min()
                    max_date = valid_dates.max()
                    st.success(f"✅ Loaded {len(processed_df)} transactions from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
                else:
                    st.success(f"✅ Loaded {len(processed_df)} transactions")
            else:
                st.success(f"✅ Loaded {len(processed_df)} transactions")
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.session_state.processed_data = None
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Show editable table if data is loaded
    if st.session_state.processed_data is not None:
        render_editable_table()


def render_save_success_screen():
    """Render the success screen after saving data."""
    result = st.session_state.save_result
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("""
    <div class='success-box'>
        <div class='success-icon'>✅</div>
        <h2 style='color: #4ECDC4 !important;'>Data Saved Successfully!</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Show merge statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>New Transactions</div>
            <div class='kpi-value'>{result['new_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        updated = result.get('updated_count', 0)
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Categories Updated</div>
            <div class='kpi-value' style='color: #2ECC71;'>{updated}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Duplicates Skipped</div>
            <div class='kpi-value' style='color: #FF6B9D;'>{result['dup_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if result.get('learned_count', 0) > 0:
        st.info(f"🧠 Learned {result['learned_count']} new category mappings!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("📤 Upload More", use_container_width=True):
                st.session_state.data_saved = False
                st.session_state.save_result = None
                st.session_state.processed_data = None
                st.rerun()
        with btn_col2:
            if st.button("📊 View Analytics", use_container_width=True, type="primary"):
                st.session_state.current_screen = "analytics"
                st.session_state.data_saved = False
                st.session_state.save_result = None
                st.rerun()


def render_editable_table():
    """Render the editable data table with category dropdowns."""
    df = st.session_state.processed_data.copy()
    
    # Format Date for display
    if 'Date' in df.columns:
        df['DateDisplay'] = df['Date'].apply(
            lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
        )
    else:
        df['DateDisplay'] = ''
    
    # Prepare display DataFrame with Date column
    display_df = df[['DateDisplay', 'Concepto', 'Amount', 'Category']].copy()
    display_df = display_df.rename(columns={'DateDisplay': 'Date'})
    
    # Count rows needing review (only expenses without category)
    needs_review_count = ((display_df['Category'].isna()) | (display_df['Category'] == '')).sum()
    expense_needs_review = ((display_df['Amount'] < 0) & ((display_df['Category'].isna()) | (display_df['Category'] == ''))).sum()
    
    if expense_needs_review > 0:
        st.warning(f"⚠️ {expense_needs_review} expenses need category assignment")
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>Review & Edit Categories</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: rgba(255,255,255,0.6);'>Click on any category to change it. Positive amounts are auto-categorized as Income (green).</p>", unsafe_allow_html=True)
    
    # Button to set all missing categories to Others
    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        if st.button("🏷️ Set All Missing to 'Others'", use_container_width=True):
            # Update display_df for rows with missing categories
            mask = (display_df['Category'].isna()) | (display_df['Category'] == '')
            display_df.loc[mask, 'Category'] = 'Others'
            # Also update session state
            st.session_state.processed_data.loc[mask, 'Category'] = 'Others'
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Editable dataframe
    edited_df = st.data_editor(
        display_df,
        column_config={
            "Date": st.column_config.TextColumn(
                "Date",
                disabled=True,
                width="small"
            ),
            "Concepto": st.column_config.TextColumn(
                "Concept",
                disabled=True,
                width="large"
            ),
            "Amount": st.column_config.NumberColumn(
                "Amount (€)",
                format="€%.2f",
                disabled=True
            ),
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=ALL_CATEGORIES,
                required=True,
                width="medium"
            )
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="category_editor"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Check for missing categories on expenses
    expenses_missing = (
        (edited_df['Amount'] < 0) & 
        ((edited_df['Category'].isna()) | (edited_df['Category'] == '') | (edited_df['Category'] == 'nan'))
    ).sum()
    
    # Save button with validation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if expenses_missing > 0:
            st.error(f"❌ Cannot save: {expenses_missing} expense(s) have no category. Please assign categories to all expenses.")
            st.button("💾 Save Transactions", use_container_width=True, type="primary", disabled=True)
        else:
            if st.button("💾 Save Transactions", use_container_width=True, type="primary"):
                save_processed_data(edited_df)


def save_processed_data(edited_df: pd.DataFrame):
    """Save the processed data with smart merging and update learned mappings."""
    user = st.session_state.selected_user
    original_df = st.session_state.processed_data.copy()
    original_categories = st.session_state.original_categories
    
    # Final validation: ensure all expenses have categories
    expenses_missing = (
        (edited_df['Amount'] < 0) & 
        ((edited_df['Category'].isna()) | (edited_df['Category'] == '') | (edited_df['Category'] == 'nan'))
    ).sum()
    
    if expenses_missing > 0:
        st.error(f"❌ Cannot save: {expenses_missing} expense(s) have no category.")
        return
    
    # Detect changed categories for learning
    new_mappings = {}
    for idx, row in edited_df.iterrows():
        concept = row['Concepto']
        new_category = row['Category']
        original_category = original_categories.get(concept, '')
        
        if new_category and new_category != original_category and new_category != 'Others':
            new_mappings[concept] = new_category
    
    # Update learned mappings
    learned_count = 0
    if new_mappings:
        update_learned_mappings(new_mappings)
        learned_count = len(new_mappings)
    
    # Merge edited categories back to original dataframe
    original_df['Category'] = edited_df['Category']
    
    # Save with smart merging (duplicate detection and category updates)
    try:
        filepath, new_count, dup_count, updated_count = add_transactions(user, original_df)
        
        # Store result for success screen
        st.session_state.save_result = {
            'filepath': filepath,
            'new_count': new_count,
            'dup_count': dup_count,
            'updated_count': updated_count,
            'learned_count': learned_count
        }
        st.session_state.data_saved = True
        st.session_state.processed_data = None
        st.rerun()
                
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")


# ============================================================================
# SCREEN 3: ANALYTICS DASHBOARD
# ============================================================================

def render_analytics_screen():
    """Render the analytics dashboard."""
    # Header with back button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state.current_screen = "home"
            st.rerun()
    with col2:
        st.markdown("<h1>📊 Analytics Dashboard</h1>", unsafe_allow_html=True)
    
    # Get available users
    users = load_users()
    
    if not users:
        st.info("No users found. Please create a user first!")
        return
    
    # Create tabs for each user (+ joint if >1 user)
    tab_names = [f"{u['emoji']} {u['name']}" for u in users]
    if len(users) > 1:
        tab_names.append("👫 Joint View")
    
    user_tabs = st.tabs(tab_names)
    
    for i, user in enumerate(users):
        with user_tabs[i]:
            render_user_analytics(user['folder'])
    
    if len(users) > 1:
        with user_tabs[-1]:
            render_joint_analytics()


def render_user_analytics(user: str):
    """Render analytics for a specific user with view tabs."""
    user_display = user.capitalize()
    data = load_user_data(user)
    
    if data.empty:
        st.info(f"No data available for {user_display}. Upload some expenses first!")
        return
    
    # View tabs - streamlined analytics (merged periods into one)
    view_tabs = st.tabs(["📈 Dashboard", "💰 Budgets", "📅 Time Periods", "🔮 Insights", "🏷️ By Category"])
    
    with view_tabs[0]:
        render_dashboard_tab(data, user_display)
    
    with view_tabs[1]:
        render_budget_tab(data, user_display)
    
    with view_tabs[2]:
        render_periods_tab(data, user_display)
    
    with view_tabs[3]:
        render_insights_tab(data, user_display)
    
    with view_tabs[4]:
        render_category_tab(data, user_display)


def render_budget_tab(data: pd.DataFrame, user_display: str):
    """Render budget management and goals tab."""
    user = user_display.lower()
    
    # Budget Alerts at the top
    alerts = get_budget_alerts(user, data)
    if alerts:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>⚠️ Budget Alerts</h3>", unsafe_allow_html=True)
        for alert in alerts:
            color = "#FF6B6B" if alert["level"] == "danger" else "#FFE66D"
            st.markdown(f"""
            <div style='background: rgba(255,107,107,0.1); border-left: 4px solid {color}; padding: 10px 15px; margin: 5px 0; border-radius: 5px;'>
                <strong style='color: {color};'>{alert['category']}</strong>: {alert['message']}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Budget Status - Progress Bars
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📊 Monthly Budget Status</h3>", unsafe_allow_html=True)
    
    budget_status = calculate_budget_status(user, data)
    
    if budget_status:
        for category, info in budget_status.items():
            # Color based on status
            if info['status'] == 'exceeded':
                bar_color = '#FF6B6B'
            elif info['status'] == 'warning':
                bar_color = '#FFE66D'
            elif info['status'] == 'caution':
                bar_color = '#F39C12'
            else:
                bar_color = '#2ECC71'
            
            percent = min(info['percent'], 100)  # Cap at 100% for display
            
            st.markdown(f"""
            <div style='margin: 15px 0;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
                    <span style='color: var(--text-primary); font-weight: 500;'>{category}</span>
                    <span style='color: var(--text-secondary);'>€{info['spent']:.0f} / €{info['budget']:.0f}</span>
                </div>
                <div style='background: rgba(255,255,255,0.1); border-radius: 10px; height: 20px; overflow: hidden;'>
                    <div style='background: {bar_color}; height: 100%; width: {percent}%; border-radius: 10px; transition: width 0.3s;'></div>
                </div>
                <div style='text-align: right; color: {bar_color}; font-size: 0.85rem;'>{info['percent']:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No budgets set. Add category budgets below to track spending!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Add/Edit Budgets
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>⚙️ Manage Budgets</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        budget_categories = [c for c in ALL_CATEGORIES if c != 'Income']
        new_budget_cat = st.selectbox("Category", budget_categories, key=f"budget_cat_{user}")
    
    with col2:
        new_budget_amount = st.number_input("Monthly Limit (€)", min_value=0.0, step=50.0, key=f"budget_amt_{user}")
    
    with col3:
        st.write("")  # Spacer
        st.write("")
        if st.button("Set Budget", key=f"set_budget_{user}"):
            if new_budget_amount > 0:
                set_category_budget(user, new_budget_cat, new_budget_amount)
                st.success(f"Budget set: {new_budget_cat} = €{new_budget_amount:.0f}/month")
                st.rerun()
    
    # Show existing budgets with delete option
    existing_budgets = get_user_budgets(user)
    if existing_budgets:
        st.markdown("<h4>Current Budgets</h4>", unsafe_allow_html=True)
        for cat, amt in existing_budgets.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(cat)
            with col2:
                st.write(f"€{amt:.0f}")
            with col3:
                if st.button("🗑️", key=f"del_budget_{user}_{cat}"):
                    remove_category_budget(user, cat)
                    st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Goals Section
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>🎯 Savings Goals</h3>", unsafe_allow_html=True)
    
    goals = calculate_goal_progress(user, data)
    
    if goals:
        for goal in goals:
            progress = goal.get('progress_percent', 0)
            color = '#2ECC71' if progress >= 100 else '#4ECDC4'
            
            st.markdown(f"""
            <div style='background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 15px; padding: 15px; margin: 10px 0;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <h4 style='margin: 0; color: var(--text-primary);'>{goal['name']}</h4>
                    <span style='color: {color}; font-weight: bold;'>€{goal['current_amount']:.0f} / €{goal['target_amount']:.0f}</span>
                </div>
                <div style='background: rgba(255,255,255,0.1); border-radius: 10px; height: 15px; margin: 10px 0; overflow: hidden;'>
                    <div style='background: {color}; height: 100%; width: {min(progress, 100)}%; border-radius: 10px;'></div>
                </div>
                <div style='display: flex; justify-content: space-between; color: var(--text-muted); font-size: 0.85rem;'>
                    <span>{progress:.0f}% complete</span>
                    <span>{"✅ Completed!" if progress >= 100 else f"€{goal['amount_remaining']:.0f} to go"}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Update/Delete buttons
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                new_amount = st.number_input("Update progress", min_value=0.0, value=goal['current_amount'], 
                                            key=f"goal_prog_{goal['id']}", step=100.0)
            with col2:
                if st.button("Update", key=f"update_goal_{goal['id']}"):
                    update_goal_progress(user, goal['id'], new_amount)
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"del_goal_{goal['id']}"):
                    delete_goal(user, goal['id'])
                    st.rerun()
    else:
        st.info("No goals yet. Add your first savings goal below!")
    
    # Add New Goal
    st.markdown("<h4>➕ Add New Goal</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        goal_name = st.text_input("Goal Name", placeholder="e.g., Summer Vacation", key=f"goal_name_{user}")
    with col2:
        goal_target = st.number_input("Target Amount (€)", min_value=0.0, step=100.0, key=f"goal_target_{user}")
    
    if st.button("Create Goal", key=f"create_goal_{user}"):
        if goal_name and goal_target > 0:
            add_goal(user, goal_name, goal_target)
            st.success(f"Goal created: {goal_name} - €{goal_target:.0f}")
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard_tab(data: pd.DataFrame, user_display: str):
    """Render dashboard with quick-glance widgets."""
    user = user_display.lower()
    
    # Time Period Selector
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col_title, col_selector = st.columns([3, 1])
    with col_title:
        st.markdown("<h3>⚡ Quick Glance</h3>", unsafe_allow_html=True)
    with col_selector:
        period_options = {
            "📊 All Time": "all_time",
            "📈 Last Year": "last_year",
            "📆 Last Month": "last_month",
            "📅 Last Week": "last_week", 
        }
        selected_period_label = st.selectbox(
            "Period",
            list(period_options.keys()),
            key=f"dashboard_period_{user}",
            label_visibility="collapsed"
        )
        selected_period = period_options[selected_period_label]
    
    # Filter data by selected period
    filtered_data = filter_data_by_period(data, selected_period)
    
    # Show message if no data in selected period
    if filtered_data.empty:
        st.info(f"No transactions found for {selected_period_label.split(' ', 1)[1]}. Try selecting a different time period.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Calculate KPIs with filtered data
    kpis = calculate_kpis(filtered_data)
    velocity = calculate_spending_velocity(filtered_data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        balance_color = '#2ECC71' if kpis['balance'] >= 0 else '#FF6B6B'
        st.markdown(f"""
        <div class='kpi-card' style='border-top: 3px solid {balance_color};'>
            <div class='kpi-label'>💰 Net Balance</div>
            <div class='kpi-value' style='color: {balance_color};'>€{kpis['balance']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='kpi-card' style='border-top: 3px solid #FF6B6B;'>
            <div class='kpi-label'>📅 Today's Rate</div>
            <div class='kpi-value' style='color: #FF6B6B;'>€{velocity['daily_rate']:.0f}/day</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='kpi-card' style='border-top: 3px solid #FFE66D;'>
            <div class='kpi-label'>📊 Month Projection</div>
            <div class='kpi-value' style='color: #FFE66D;'>€{velocity['projected_month']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        savings_color = '#2ECC71' if kpis['savings_rate'] >= 20 else '#FFE66D' if kpis['savings_rate'] >= 0 else '#FF6B6B'
        st.markdown(f"""
        <div class='kpi-card' style='border-top: 3px solid {savings_color};'>
            <div class='kpi-label'>💎 Savings Rate</div>
            <div class='kpi-value' style='color: {savings_color};'>{kpis['savings_rate']:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Budget Alerts Widget
    alerts = get_budget_alerts(user, filtered_data)
    if alerts:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>🔔 Budget Alerts</h3>", unsafe_allow_html=True)
        for alert in alerts[:3]:
            color = "#FF6B6B" if alert["level"] == "danger" else "#FFE66D"
            st.markdown(f"""
            <div style='background: rgba(255,107,107,0.1); border-left: 4px solid {color}; padding: 10px 15px; margin: 5px 0; border-radius: 5px;'>
                <strong style='color: {color};'>{alert['category']}</strong>: {alert['message']}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Income vs Expenses Chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig = create_category_pie_chart(filtered_data, f"Expenses by Category")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig = create_income_expense_trend(filtered_data, f"Income vs Expenses")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Category Breakdown Table
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>🏷️ Top Spending Categories</h3>", unsafe_allow_html=True)
    breakdown = get_category_breakdown(filtered_data)
    if not breakdown.empty:
        breakdown = breakdown.head(5)  # Top 5 only for dashboard
        breakdown['Amount'] = breakdown['Amount'].apply(lambda x: f"€{x:,.2f}")
        breakdown['Percent'] = breakdown['Percent'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(breakdown, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Transaction Explorer
    render_transaction_explorer(filtered_data, user_display)


def render_periods_tab(data: pd.DataFrame, user_display: str):
    """Render unified time periods tab with Daily/Monthly/Annual/Calendar views."""
    
    # Period selector
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    period_view = st.radio(
        "View Period",
        ["📅 Daily", "📆 Monthly", "📊 Annual", "🗓️ Calendar"],
        horizontal=True,
        key=f"period_view_{user_display}"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    if period_view == "📅 Daily":
        render_daily_tab(data, user_display)
    elif period_view == "📆 Monthly":
        render_monthly_tab(data, user_display)
    elif period_view == "📊 Annual":
        render_annual_tab(data, user_display)
    else:
        render_calendar_tab(data, user_display)


def render_insights_tab(data: pd.DataFrame, user_display: str):
    """Render insights tab with recurring transactions and predictions."""
    user = user_display.lower()
    
    # Spending Velocity Widget
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📈 Spending Velocity</h3>", unsafe_allow_html=True)
    
    velocity = calculate_spending_velocity(data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Daily Rate</div>
            <div class='kpi-value'>€{velocity['daily_rate']:.0f}</div>
            <div style='color: var(--text-muted);'>per day</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Spent So Far</div>
            <div class='kpi-value' style='color: #FF6B6B;'>€{velocity['current_spent']:.0f}</div>
            <div style='color: var(--text-muted);'>this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Projected</div>
            <div class='kpi-value' style='color: #FFE66D;'>€{velocity['projected_month']:.0f}</div>
            <div style='color: var(--text-muted);'>by month end</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>Days Left</div>
            <div class='kpi-value'>{velocity['days_remaining']}</div>
            <div style='color: var(--text-muted);'>in this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Anomaly Alerts
    anomalies = detect_anomalies(data)
    if anomalies:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>⚠️ Spending Anomalies</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: var(--text-muted);'>Categories where you're spending more than usual</p>", unsafe_allow_html=True)
        
        for anomaly in anomalies[:5]:
            color = "#FF6B6B" if anomaly['percent_above'] > 50 else "#FFE66D"
            st.markdown(f"""
            <div style='background: var(--bg-card); border-left: 4px solid {color}; padding: 15px; margin: 10px 0; border-radius: 5px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <strong style='color: var(--text-primary);'>{anomaly['category']}</strong>
                    <span style='color: {color}; font-weight: bold;'>+{anomaly['percent_above']:.0f}% above avg</span>
                </div>
                <div style='color: var(--text-muted); margin-top: 5px;'>
                    €{anomaly['current_amount']:.0f} this month vs €{anomaly['average_amount']:.0f} average (€{anomaly['extra_spent']:.0f} extra)
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recurring Transactions
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>🔄 Recurring Transactions</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--text-muted);'>Detected subscriptions and fixed costs</p>", unsafe_allow_html=True)
    
    recurring = detect_recurring_transactions(data)
    
    if recurring:
        fixed_costs = get_monthly_fixed_costs(recurring)
        st.markdown(f"""
        <div style='background: var(--bg-card); border-radius: 10px; padding: 15px; margin-bottom: 15px;'>
            <span style='color: var(--text-muted);'>Estimated Monthly Fixed Costs:</span>
            <span style='color: #FF6B6B; font-size: 1.5rem; font-weight: bold; margin-left: 10px;'>€{fixed_costs:.0f}</span>
        </div>
        """, unsafe_allow_html=True)
        
        for item in recurring[:10]:
            color = "#FF6B6B" if item['is_expense'] else "#2ECC71"
            freq_icon = {"monthly": "📅", "weekly": "📆", "yearly": "📆", "bi-weekly": "📆", "quarterly": "📆"}.get(item['frequency'], "🔁")
            
            st.markdown(f"""
            <div style='background: var(--bg-card); border-radius: 10px; padding: 12px; margin: 8px 0; border: 1px solid var(--border-color);'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <span style='font-weight: 500; color: var(--text-primary);'>{item['concept'][:40]}{'...' if len(item['concept']) > 40 else ''}</span>
                        <span style='background: var(--bg-card); padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; margin-left: 10px;'>{item['category']}</span>
                    </div>
                    <span style='color: {color}; font-weight: bold;'>€{item['amount']:.2f}</span>
                </div>
                <div style='color: var(--text-muted); font-size: 0.85rem; margin-top: 5px;'>
                    {freq_icon} {item['frequency'].capitalize()} • Last: {item['last_date']} • Next expected: {item['next_expected']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Not enough data to detect recurring transactions. Keep tracking to see patterns!")
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_calendar_tab(data: pd.DataFrame, user_display: str):
    """Render bill calendar tab with monthly calendar view."""
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📅 Bill Calendar</h3>", unsafe_allow_html=True)
    
    # Month/Year selector
    now = datetime.now()
    data = data.copy()
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    valid_dates = data['Date'].dropna()
    
    if valid_dates.empty:
        st.info("No transactions with dates available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    col1, col2 = st.columns(2)
    with col1:
        years = sorted(valid_dates.dt.year.unique(), reverse=True)
        selected_year = st.selectbox("Year", years, key=f"cal_year_{user_display}")
    with col2:
        months = list(range(1, 13))
        month_names = {i: calendar.month_name[i] for i in range(1, 13)}
        selected_month = st.selectbox("Month", months, format_func=lambda x: month_names[x], 
                                      index=now.month-1, key=f"cal_month_{user_display}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Calendar grid using Streamlit columns
    cal_data = get_transaction_calendar(data, selected_year, selected_month)
    
    # Get first day of month and number of days
    first_day = datetime(selected_year, selected_month, 1)
    start_weekday = first_day.weekday()  # Monday = 0
    
    # Calculate days in month
    if selected_month == 12:
        next_month = datetime(selected_year + 1, 1, 1)
    else:
        next_month = datetime(selected_year, selected_month + 1, 1)
    days_in_month = (next_month - timedelta(days=1)).day
    
    # Calendar header
    header_cols = st.columns(7)
    days_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, col in enumerate(header_cols):
        with col:
            color = "#FF6B9D" if i >= 5 else "rgba(255,255,255,0.6)"
            st.markdown(f"<div style='text-align: center; font-weight: 600; color: {color};'>{days_names[i]}</div>", 
                       unsafe_allow_html=True)
    
    # Build calendar grid - 6 rows max
    all_days = [None] * start_weekday + list(range(1, days_in_month + 1))
    
    # Pad to complete last week
    while len(all_days) % 7 != 0:
        all_days.append(None)
    
    # Render weeks
    for week_start in range(0, len(all_days), 7):
        week_days = all_days[week_start:week_start + 7]
        cols = st.columns(7)
        
        for i, day in enumerate(week_days):
            with cols[i]:
                if day is None:
                    st.markdown("<div style='height: 70px;'></div>", unsafe_allow_html=True)
                else:
                    transactions = cal_data.get(day, [])
                    
                    if transactions:
                        total = sum(t['amount'] for t in transactions)
                        color = "#FF6B6B" if total < 0 else "#2ECC71"
                        dot_count = min(len(transactions), 4)
                        dots = "•" * dot_count
                        
                        st.markdown(f"""
                        <div style='background: rgba(255,255,255,0.05); border-radius: 8px; padding: 8px; 
                                    text-align: center; border: 1px solid rgba(255,255,255,0.1); min-height: 70px;'>
                            <div style='color: white; font-weight: 500;'>{day}</div>
                            <div style='color: {color}; font-size: 0.85rem; font-weight: 600;'>€{abs(total):.0f}</div>
                            <div style='color: {color}; font-size: 0.7rem;'>{dots}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='background: rgba(255,255,255,0.02); border-radius: 8px; padding: 8px; 
                                    text-align: center; border: 1px solid rgba(255,255,255,0.05); min-height: 70px; opacity: 0.5;'>
                            <div style='color: rgba(255,255,255,0.5);'>{day}</div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Show selected day details
    st.markdown("<h4 style='margin-top: 20px;'>📋 Transactions This Month</h4>", unsafe_allow_html=True)
    
    month_total_income = 0
    month_total_expense = 0
    
    for day in sorted(cal_data.keys()):
        for tx in cal_data[day]:
            if tx['amount'] > 0:
                month_total_income += tx['amount']
            else:
                month_total_expense += abs(tx['amount'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Income</div><div class='kpi-value' style='color: #2ECC71;'>€{month_total_income:.0f}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Expenses</div><div class='kpi-value' style='color: #FF6B6B;'>€{month_total_expense:.0f}</div></div>", unsafe_allow_html=True)
    with col3:
        balance = month_total_income - month_total_expense
        color = "#2ECC71" if balance >= 0 else "#FF6B6B"
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Balance</div><div class='kpi-value' style='color: {color};'>€{balance:.0f}</div></div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_overview_tab(data: pd.DataFrame, user_display: str):
    """Render overview tab with comprehensive financial KPIs and charts."""
    kpis = calculate_kpis(data)
    
    # Financial Summary KPIs - 4 key metrics
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>💰 Financial Summary</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card' style='border-left: 4px solid #2ECC71;'>
            <div class='kpi-label'>Total Income</div>
            <div class='kpi-value' style='color: #2ECC71;'>€{kpis['total_income']:,.2f}</div>
            <div style='color: rgba(255,255,255,0.5);'>{kpis['income_count']} transactions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='kpi-card' style='border-left: 4px solid #FF6B6B;'>
            <div class='kpi-label'>Total Expenses</div>
            <div class='kpi-value' style='color: #FF6B6B;'>€{kpis['total_expenses']:,.2f}</div>
            <div style='color: rgba(255,255,255,0.5);'>{kpis['expense_count']} transactions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        balance_color = '#4ECDC4' if kpis['balance'] >= 0 else '#FF6B9D'
        balance_icon = '📈' if kpis['balance'] >= 0 else '📉'
        st.markdown(f"""
        <div class='kpi-card' style='border-left: 4px solid {balance_color};'>
            <div class='kpi-label'>Net Balance {balance_icon}</div>
            <div class='kpi-value' style='color: {balance_color};'>€{kpis['balance']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        savings_color = '#2ECC71' if kpis['savings_rate'] >= 20 else '#FFE66D' if kpis['savings_rate'] >= 0 else '#FF6B6B'
        st.markdown(f"""
        <div class='kpi-card' style='border-left: 4px solid {savings_color};'>
            <div class='kpi-label'>Savings Rate</div>
            <div class='kpi-value' style='color: {savings_color};'>{kpis['savings_rate']:.1f}%</div>
            <div style='color: rgba(255,255,255,0.5);'>of income saved</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Charts row - Pie chart and Income vs Expenses trend
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig = create_category_pie_chart(data, f"{user_display}'s Expenses by Category")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig = create_income_expense_trend(data, f"{user_display}'s Income vs Expenses")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Category breakdown table
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>🏷️ Expense Breakdown by Category</h3>", unsafe_allow_html=True)
    
    breakdown = get_category_breakdown(data)
    if not breakdown.empty:
        # Format for display
        breakdown['Amount'] = breakdown['Amount'].apply(lambda x: f"€{x:,.2f}")
        breakdown['Percent'] = breakdown['Percent'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(breakdown, use_container_width=True, hide_index=True)
    else:
        st.info("No expense data available")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Transaction Explorer
    render_transaction_explorer(data, user_display)


def render_transaction_explorer(data: pd.DataFrame, user_display: str):
    """Render a searchable, filterable, editable transaction explorer with row selection."""
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📋 Transaction Explorer</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: rgba(255,255,255,0.6);'>Search, filter, and edit transactions. Check rows to see sum of selected amounts.</p>", unsafe_allow_html=True)
    
    # Prepare data for display
    display_data = data.copy()
    display_data['Date'] = pd.to_datetime(display_data['Date'], errors='coerce')
    
    # Filter controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search = st.text_input("🔍 Search", placeholder="Search concept...", key=f"search_{user_display}")
    
    with col2:
        categories = ['All'] + sorted(display_data['Category'].dropna().unique().tolist())
        selected_category = st.selectbox("Category", categories, key=f"filter_cat_{user_display}")
    
    with col3:
        type_options = ['All', 'Expenses Only', 'Income Only']
        selected_type = st.selectbox("Type", type_options, key=f"filter_type_{user_display}")
    
    with col4:
        sort_options = ['Date (Newest)', 'Date (Oldest)', 'Amount (High→Low)', 'Amount (Low→High)', 'Category']
        selected_sort = st.selectbox("Sort by", sort_options, key=f"sort_{user_display}")
    
    # Apply filters
    filtered = display_data.copy()
    
    if search:
        filtered = filtered[filtered['Concepto'].str.contains(search, case=False, na=False)]
    
    if selected_category != 'All':
        filtered = filtered[filtered['Category'] == selected_category]
    
    if selected_type == 'Expenses Only':
        filtered = filtered[filtered['Amount'] < 0]
    elif selected_type == 'Income Only':
        filtered = filtered[filtered['Amount'] > 0]
    
    # Sort
    if selected_sort == 'Date (Newest)':
        filtered = filtered.sort_values('Date', ascending=False)
    elif selected_sort == 'Date (Oldest)':
        filtered = filtered.sort_values('Date', ascending=True)
    elif selected_sort == 'Amount (High→Low)':
        filtered = filtered.sort_values('Amount', ascending=False)
    elif selected_sort == 'Amount (Low→High)':
        filtered = filtered.sort_values('Amount', ascending=True)
    elif selected_sort == 'Category':
        filtered = filtered.sort_values('Category', ascending=True)
    
    # Prepare display columns
    if 'Date' in filtered.columns:
        filtered['DateDisplay'] = filtered['Date'].apply(
            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
        )
    
    # Add Select column for row selection
    display_df = filtered[['DateDisplay', 'Concepto', 'Amount', 'Category']].copy().reset_index(drop=True)
    display_df = display_df.rename(columns={'DateDisplay': 'Date'})
    display_df.insert(0, 'Select', False)  # Add checkbox column at start
    
    # Show count
    st.markdown(f"<p style='color: rgba(255,255,255,0.6);'>Showing <b>{len(display_df)}</b> of {len(data)} transactions. Check rows to sum amounts.</p>", 
                unsafe_allow_html=True)
    
    # Editable dataframe with selection
    edited_df = st.data_editor(
        display_df,
        column_config={
            "Select": st.column_config.CheckboxColumn("✓", default=False, width="small"),
            "Date": st.column_config.TextColumn("Date", disabled=True, width="small"),
            "Concepto": st.column_config.TextColumn("Concept", disabled=True, width="large"),
            "Amount": st.column_config.NumberColumn("Amount (€)", format="€%.2f", disabled=True),
            "Category": st.column_config.SelectboxColumn("Category", options=ALL_CATEGORIES, required=True, width="medium")
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key=f"tx_explorer_{user_display}"
    )
    
    # Calculate and display sum of selected rows
    selected_rows = edited_df[edited_df['Select'] == True]
    if not selected_rows.empty:
        selected_sum = selected_rows['Amount'].sum()
        selected_count = len(selected_rows)
        
        # Display sum in red at bottom right
        sum_color = '#FF6B6B' if selected_sum < 0 else '#2ECC71'
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-end; align-items: center; margin-top: 10px;'>
            <div style='background: rgba(0,0,0,0.3); padding: 12px 20px; border-radius: 8px; border: 2px solid {sum_color};'>
                <span style='color: rgba(255,255,255,0.7); margin-right: 15px;'>{selected_count} selected</span>
                <span style='color: {sum_color}; font-size: 1.4rem; font-weight: bold;'>Σ €{selected_sum:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Check for category changes and save
    original_categories = display_df['Category']
    edited_categories = edited_df['Category']
    
    if not original_categories.equals(edited_categories):
        changed_mask = original_categories != edited_categories
        if changed_mask.any():
            changes = {}
            for idx in display_df[changed_mask].index:
                concept = edited_df.loc[idx, 'Concepto']
                new_cat = edited_df.loc[idx, 'Category']
                if new_cat and new_cat != 'Others':
                    changes[concept] = new_cat
            
            if changes:
                if st.button("💾 Save Category Changes", type="primary", key=f"save_changes_{user_display}"):
                    from storage import update_learned_mappings, load_user_data, save_user_data
                    
                    update_learned_mappings(changes)
                    
                    user_data = load_user_data(user_display.lower())
                    for concept, new_cat in changes.items():
                        user_data.loc[user_data['Concepto'] == concept, 'Category'] = new_cat
                    save_user_data(user_display.lower(), user_data)
                    
                    st.success(f"✅ Updated {len(changes)} category mapping(s)!")
                    st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_daily_tab(data: pd.DataFrame, user_display: str):
    """Render daily view tab with date range filtering."""
    data = data.copy()
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    valid_dates = data['Date'].dropna()
    
    if valid_dates.empty:
        st.info("No data with dates available.")
        return
    
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    
    # Date range filter
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📅 Date Range Filter</h3>", unsafe_allow_html=True)
    
    # Quick filter buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Calculate date ranges for quick filters
    from datetime import timedelta
    today = datetime.now().date()
    
    with col1:
        last_30 = st.button("Last 30 Days", key=f"last30_{user_display}", use_container_width=True)
    with col2:
        last_90 = st.button("Last 3 Months", key=f"last90_{user_display}", use_container_width=True)
    with col3:
        last_year = st.button("Last Year", key=f"lastyear_{user_display}", use_container_width=True)
    with col4:
        all_time = st.button("All Time", key=f"alltime_{user_display}", use_container_width=True)
    with col5:
        custom = st.button("Custom Range", key=f"custom_{user_display}", use_container_width=True)
    
    # Initialize date range in session state
    range_key = f"daily_range_{user_display}"
    if range_key not in st.session_state:
        st.session_state[range_key] = (min_date, max_date)  # Default: all time
    
    # Handle button clicks
    if last_30:
        st.session_state[range_key] = (max(min_date, today - timedelta(days=30)), max_date)
    elif last_90:
        st.session_state[range_key] = (max(min_date, today - timedelta(days=90)), max_date)
    elif last_year:
        st.session_state[range_key] = (max(min_date, today - timedelta(days=365)), max_date)
    elif all_time:
        st.session_state[range_key] = (min_date, max_date)
    
    # Custom date picker
    show_picker_key = f"show_picker_{user_display}"
    if custom:
        st.session_state[show_picker_key] = True
    
    if st.session_state.get(show_picker_key, False):
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start Date", value=st.session_state[range_key][0], 
                                  min_value=min_date, max_value=max_date,
                                  key=f"start_{user_display}")
        with col2:
            end = st.date_input("End Date", value=st.session_state[range_key][1],
                               min_value=min_date, max_value=max_date,
                               key=f"end_{user_display}")
        st.session_state[range_key] = (start, end)
    
    start_date, end_date = st.session_state[range_key]
    st.markdown(f"<p style='color: rgba(255,255,255,0.6);'>Showing data from <b>{start_date}</b> to <b>{end_date}</b></p>", 
                unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Convert to datetime for filtering
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    
    # Daily chart
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    fig = create_daily_chart_all(data, start_dt, end_dt)
    st.plotly_chart(fig, use_container_width=True)
    
    # Daily summary table
    summary = get_daily_summary(data, start_dt, end_dt)
    if not summary.empty:
        st.markdown("<h4>Daily Summary</h4>", unsafe_allow_html=True)
        # Format for display
        for col in ['Income', 'Expenses', 'Net', 'Cumulative']:
            if col in summary.columns:
                summary[col] = summary[col].apply(lambda x: f"€{x:,.2f}")
        st.dataframe(summary, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_monthly_tab(data: pd.DataFrame, user_display: str):
    """Render monthly view tab."""
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    # Year selector
    years = get_available_years(user_display.lower())
    
    if not years:
        st.info("No data with dates available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Add "All Years" option
    year_options = ["All Years"] + years
    selected = st.selectbox("Filter by Year", year_options, key=f"monthly_year_{user_display}")
    
    selected_year = None if selected == "All Years" else selected
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Monthly chart
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    fig = create_monthly_chart(data, selected_year)
    st.plotly_chart(fig, use_container_width=True)
    
    # Monthly summary table
    summary = get_monthly_summary(data, selected_year)
    if not summary.empty:
        st.markdown("<h4>Monthly Summary</h4>", unsafe_allow_html=True)
        st.dataframe(summary, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_annual_tab(data: pd.DataFrame, user_display: str):
    """Render annual view tab."""
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    # Annual chart
    fig = create_annual_chart(data)
    st.plotly_chart(fig, use_container_width=True)
    
    # Annual summary table
    summary = get_annual_summary(data)
    if not summary.empty:
        st.markdown("<h4>Annual Summary</h4>", unsafe_allow_html=True)
        st.dataframe(summary, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_category_tab(data: pd.DataFrame, user_display: str):
    """Render category view tab."""
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    # Period selector for breakdown
    period = st.radio(
        "Group by",
        ["Month", "Year"],
        horizontal=True,
        key=f"category_period_{user_display}"
    )
    period_val = period.lower()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Category breakdown chart
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    fig = create_category_breakdown_chart(data, period_val)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Category trend for selected category
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    if 'Category' in data.columns:
        categories = sorted(data['Category'].dropna().unique())
        if categories:
            selected_category = st.selectbox(
                "View trend for category",
                categories,
                key=f"category_trend_{user_display}"
            )
            
            fig = create_category_trend(data, selected_category)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Category summary table
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    summary = get_category_summary(data)
    if not summary.empty:
        st.markdown("<h4>Category Summary</h4>", unsafe_allow_html=True)
        st.dataframe(summary, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_joint_analytics():
    """Render joint analytics comparing all users."""
    users = load_users()
    
    if len(users) < 2:
        st.info("Joint analytics requires at least 2 users.")
        return
    
    # Load data for all users
    all_user_data = {}
    for user in users:
        data = load_user_data(user['folder'])
        if not data.empty:
            all_user_data[user['name']] = data
    
    if not all_user_data:
        st.info("No data available. Upload expenses for at least one user.")
        return
    
    # Summary comparison
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    masha_total = masha_data[masha_data['Amount'] < 0]['Amount'].abs().sum() if not masha_data.empty and 'Amount' in masha_data.columns else 0
    pablo_total = pablo_data[pablo_data['Amount'] < 0]['Amount'].abs().sum() if not pablo_data.empty and 'Amount' in pablo_data.columns else 0
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card' style='border-color: rgba(255, 107, 157, 0.4);'>
            <div class='kpi-label'>👩 Masha Total</div>
            <div class='kpi-value' style='color: #FF6B9D;'>€{masha_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='kpi-card' style='border-color: rgba(78, 205, 196, 0.4);'>
            <div class='kpi-label'>👨 Pablo Total</div>
            <div class='kpi-value'>€{pablo_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Comparison bar chart
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    fig = create_comparison_bar_chart(masha_data, pablo_data)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    # Apply styles first (for login page too)
    apply_custom_styles()
    
    # Check authentication - show login if not authenticated
    if not check_password():
        return
    
    # Auto-create/get user from OAuth email
    user_email = st.session_state.get("user_email", "")
    user_email = st.session_state.get("user_email", "")
    user_name = st.session_state.get("user_name", "")
    
    # Multi-tenant: Get or create account for this email
    if user_email and is_cloud_mode():
        account = get_or_create_account(user_email)
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
        render_user_home(st.session_state.get("selected_data_user_id", ""))
    elif current_screen == 'upload':
        render_upload_screen()
    elif current_screen == 'analytics':
        render_analytics_screen()
    elif current_screen == 'joint_analytics':
        render_joint_analytics_screen()
    else:
        st.session_state.current_screen = 'home'
        st.rerun()


if __name__ == "__main__":
    main()
