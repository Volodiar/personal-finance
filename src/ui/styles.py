import streamlit as st

def apply_custom_styles():
    """Apply glassmorphism and modern styling with theme support."""
    # Get current theme from session state
    is_dark = st.session_state.get('theme', 'dark') == 'dark'

    # Theme-specific CSS variables
    if is_dark:
        theme_vars = """
        :root {
            --bg-primary: #0f0f1a;
            --bg-secondary: #141428;
            --bg-tertiary: #1a1a3e;
            --bg-card: rgba(255, 255, 255, 0.06);
            --bg-card-hover: rgba(255, 255, 255, 0.12);
            --text-primary: #f0f0f5;
            --text-secondary: rgba(255, 255, 255, 0.72);
            --text-muted: rgba(255, 255, 255, 0.45);
            --border-color: rgba(255, 255, 255, 0.09);
            --accent-primary: #4ECDC4;
            --accent-secondary: #44A08D;
            --accent-pink: #FF6B9D;
            --danger: #FF6B6B;
            --success: #2ECC71;
            --warning: #FFE66D;
            --shadow: rgba(0, 0, 0, 0.45);
            --gradient-1: rgba(78, 205, 196, 0.08);
            --gradient-2: rgba(255, 107, 157, 0.06);
            --card-glow: rgba(78, 205, 196, 0.25);
        }
        """
    else:
        theme_vars = """
        :root {
            --bg-primary: #f0f2f8;
            --bg-secondary: #e6e9f2;
            --bg-tertiary: #dce0ed;
            --bg-card: rgba(255, 255, 255, 0.85);
            --bg-card-hover: rgba(255, 255, 255, 1);
            --text-primary: #1a1a2e;
            --text-secondary: rgba(26, 26, 46, 0.72);
            --text-muted: rgba(26, 26, 46, 0.45);
            --border-color: rgba(0, 0, 0, 0.08);
            --accent-primary: #3DBDB5;
            --accent-secondary: #2E8B7A;
            --accent-pink: #E85A8A;
            --danger: #E74C3C;
            --success: #27AE60;
            --warning: #F1C40F;
            --shadow: rgba(0, 0, 0, 0.08);
            --gradient-1: rgba(61, 189, 181, 0.08);
            --gradient-2: rgba(232, 90, 138, 0.06);
            --card-glow: rgba(61, 189, 181, 0.2);
        }
        """

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    {theme_vars}

    /* ============================================
       GLOBAL STYLES
       ============================================ */
    .stApp {{
        background: linear-gradient(160deg, var(--bg-primary) 0%, var(--bg-secondary) 40%, var(--bg-tertiary) 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* ============================================
       GLASSMORPHISM CARD
       ============================================ */
    .glass-card {{
        background: var(--bg-card);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 20px;
        border: 1px solid var(--border-color);
        padding: 1.75rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px var(--shadow), inset 0 1px 0 rgba(255,255,255,0.05);
        transition: box-shadow 0.3s ease, transform 0.3s ease;
    }}
    .glass-card:hover {{
        box-shadow: 0 12px 40px var(--shadow), inset 0 1px 0 rgba(255,255,255,0.08);
    }}

    /* ============================================
       METRIC CARD (KPI with accent top border)
       ============================================ */
    .metric-card {{
        background: var(--bg-card);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        border-top: 3px solid var(--accent-primary);
        padding: 1.25rem 1rem;
        text-align: center;
        box-shadow: 0 4px 20px var(--shadow);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 28px var(--shadow);
    }}

    /* ============================================
       USER / PROFILE CARD
       ============================================ */
    .user-card {{
        background: var(--bg-card);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-radius: 20px;
        border: 1px solid var(--border-color);
        padding: 2rem 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px var(--shadow);
        transition: all 0.3s ease;
    }}
    .user-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 36px var(--shadow), 0 0 20px var(--card-glow);
        border-color: var(--accent-primary);
    }}
    .user-card .card-emoji {{
        font-size: 2.5rem;
        display: block;
        margin-bottom: 0.75rem;
    }}
    .user-card .card-name {{
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
    }}

    /* ============================================
       UPLOAD ZONE
       ============================================ */
    .upload-zone {{
        background: linear-gradient(135deg, var(--gradient-1), var(--gradient-2));
        backdrop-filter: blur(12px);
        border: 2px dashed var(--border-color);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }}
    .upload-zone:hover {{
        border-color: var(--accent-primary);
        box-shadow: 0 0 24px var(--card-glow);
    }}

    /* ============================================
       PROFILE BUTTONS (legacy compatibility)
       ============================================ */
    .profile-btn {{
        background: linear-gradient(135deg, rgba(255, 107, 157, 0.2) 0%, rgba(255, 107, 157, 0.06) 100%);
        backdrop-filter: blur(12px);
        border: 1.5px solid rgba(255, 107, 157, 0.3);
        border-radius: 20px;
        padding: 2.5rem 1.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        color: var(--text-primary);
    }}
    .profile-btn:hover {{
        transform: translateY(-5px);
        box-shadow: 0 12px 36px rgba(255, 107, 157, 0.25);
        border-color: rgba(255, 107, 157, 0.7);
    }}
    .profile-btn.pablo {{
        background: linear-gradient(135deg, rgba(78, 205, 196, 0.2) 0%, rgba(78, 205, 196, 0.06) 100%);
        border-color: rgba(78, 205, 196, 0.3);
    }}
    .profile-btn.pablo:hover {{
        box-shadow: 0 12px 36px rgba(78, 205, 196, 0.25);
        border-color: rgba(78, 205, 196, 0.7);
    }}

    /* ============================================
       KPI CARDS
       ============================================ */
    .kpi-card {{
        background: var(--bg-card);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 16px var(--shadow);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 24px var(--shadow);
    }}
    .kpi-value {{
        font-size: 1.85rem;
        font-weight: 700;
        color: var(--accent-primary);
        margin: 0.4rem 0;
        letter-spacing: -0.5px;
    }}
    .kpi-label {{
        font-size: 0.8rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 500;
    }}

    /* ============================================
       NAV PILL
       ============================================ */
    .nav-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        color: var(--text-secondary);
        font-size: 0.88rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.25s ease;
        text-decoration: none;
    }}
    .nav-pill:hover {{
        background: var(--bg-card-hover);
        border-color: var(--accent-primary);
        color: var(--accent-primary);
        transform: translateY(-1px);
    }}

    /* ============================================
       BADGE
       ============================================ */
    .badge {{
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }}
    .badge-success {{
        background: rgba(46, 204, 113, 0.15);
        color: var(--success);
        border: 1px solid rgba(46, 204, 113, 0.3);
    }}
    .badge-warning {{
        background: rgba(255, 230, 109, 0.15);
        color: var(--warning);
        border: 1px solid rgba(255, 230, 109, 0.3);
    }}
    .badge-danger {{
        background: rgba(255, 107, 107, 0.15);
        color: var(--danger);
        border: 1px solid rgba(255, 107, 107, 0.3);
    }}

    /* ============================================
       ALERT CARD
       ============================================ */
    .alert-card {{
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 0.85rem 1.1rem;
        margin: 0.4rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.9rem;
    }}
    .alert-card-danger {{
        background: rgba(255, 107, 107, 0.1);
        border-left: 4px solid var(--danger);
        color: var(--text-secondary);
    }}
    .alert-card-warning {{
        background: rgba(255, 230, 109, 0.1);
        border-left: 4px solid var(--warning);
        color: var(--text-secondary);
    }}
    .alert-card-success {{
        background: rgba(46, 204, 113, 0.1);
        border-left: 4px solid var(--success);
        color: var(--text-secondary);
    }}
    .alert-card-info {{
        background: rgba(78, 205, 196, 0.1);
        border-left: 4px solid var(--accent-primary);
        color: var(--text-secondary);
    }}

    /* ============================================
       TYPOGRAPHY
       ============================================ */
    h1 {{
        color: var(--text-primary) !important;
        font-weight: 800 !important;
        text-align: center;
        margin-bottom: 1.5rem !important;
        letter-spacing: -0.5px;
    }}
    h2 {{
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }}
    h3 {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}
    p, label, span {{
        color: var(--text-secondary);
    }}
    .header-text {{
        text-align: center;
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--text-primary) !important;
        margin-bottom: 0.25rem;
    }}
    .sub-header-text {{
        text-align: center;
        color: var(--text-muted) !important;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }}
    .animated-title {{
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-pink), var(--accent-primary));
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradient-shift 4s ease infinite;
        text-align: center;
    }}
    @keyframes gradient-shift {{
        0% {{ background-position: 0% center; }}
        50% {{ background-position: 100% center; }}
        100% {{ background-position: 0% center; }}
    }}

    /* ============================================
       BUTTONS
       ============================================ */
    .stButton > button {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        min-height: 44px;
        box-shadow: 0 4px 14px rgba(78, 205, 196, 0.25);
        letter-spacing: 0.2px;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(78, 205, 196, 0.4);
        filter: brightness(1.08);
    }}
    .stButton > button:active {{
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(78, 205, 196, 0.3);
    }}

    .stLinkButton > a {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px rgba(78, 205, 196, 0.25) !important;
    }}
    .stLinkButton > a:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(78, 205, 196, 0.4) !important;
        filter: brightness(1.08) !important;
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

    /* ============================================
       STREAMLIT OVERRIDES
       ============================================ */
    .stDataFrame {{
        background: var(--bg-card);
        border-radius: 12px;
    }}

    /* File uploader */
    .stFileUploader {{
        background: var(--bg-card);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid var(--border-color);
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.4rem;
        background: var(--bg-card);
        border-radius: 14px;
        padding: 0.4rem;
        border: 1px solid var(--border-color);
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px;
        color: var(--text-secondary);
        padding: 0.55rem 1rem;
        min-height: 42px;
        font-weight: 500;
        transition: all 0.25s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background: var(--bg-card-hover);
        color: var(--text-primary);
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
        color: white !important;
        font-weight: 600;
    }}

    /* Success message styling */
    .success-box {{
        background: rgba(78, 205, 196, 0.12);
        border: 2px solid rgba(78, 205, 196, 0.4);
        border-radius: 16px;
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
        min-height: 44px;
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }}
    .stTextInput input:focus, .stDateInput input:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px var(--card-glow) !important;
    }}

    /* Selectbox dropdown */
    .stSelectbox > div > div {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        transition: border-color 0.25s ease;
    }}
    .stSelectbox > div > div:hover {{
        border-color: var(--accent-primary) !important;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: var(--bg-card) !important;
        backdrop-filter: blur(16px);
        border-right: 1px solid var(--border-color);
    }}
    section[data-testid="stSidebar"] .stButton > button {{
        background: transparent;
        border: 1px solid var(--border-color);
        color: var(--text-secondary) !important;
        box-shadow: none;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: var(--bg-card-hover);
        border-color: var(--accent-primary);
        color: var(--accent-primary) !important;
        box-shadow: none;
    }}

    /* Improved grid handling */
    .stColumns > div {{
        min-width: 0;
    }}

    /* Expander styling */
    .streamlit-expanderHeader {{
        background: var(--bg-card) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        font-weight: 500;
    }}

    /* ============================================
       RESPONSIVE BREAKPOINTS
       ============================================ */

    /* Desktop large screens */
    @media (min-width: 1200px) {{
        .glass-card {{
            padding: 2.25rem;
        }}
        .kpi-value {{
            font-size: 2rem;
        }}
    }}

    /* Tablet (768px - 1024px) */
    @media (min-width: 768px) and (max-width: 1024px) {{
        .glass-card {{
            padding: 1.5rem;
            margin: 0.75rem 0;
        }}
        .kpi-card {{
            padding: 1rem;
        }}
        .kpi-value {{
            font-size: 1.5rem;
        }}
        .kpi-label {{
            font-size: 0.75rem;
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
        .kpi-card, .metric-card {{
            padding: 0.85rem;
            margin-bottom: 0.5rem;
        }}
        .kpi-value {{
            font-size: 1.3rem;
        }}
        .kpi-label {{
            font-size: 0.72rem;
            letter-spacing: 0.5px;
        }}
        .profile-btn, .user-card {{
            padding: 1.5rem 1rem;
        }}
        h1 {{
            font-size: 1.5rem !important;
            margin-bottom: 1rem !important;
        }}
        h3 {{
            font-size: 1.1rem !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            overflow-x: auto;
            flex-wrap: nowrap;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            -ms-overflow-style: none;
            padding-bottom: 5px;
        }}
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {{
            display: none;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 0.8rem;
            padding: 0.4rem 0.8rem;
            white-space: nowrap;
            flex-shrink: 0;
        }}
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
        .kpi-card, .metric-card {{
            padding: 0.7rem;
        }}
        .kpi-value {{
            font-size: 1.15rem;
        }}
        .kpi-label {{
            font-size: 0.68rem;
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
        .js-plotly-plot {{
            max-width: 100% !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)
