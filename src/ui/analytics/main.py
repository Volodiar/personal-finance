import streamlit as st
import pandas as pd
from services.factory import get_data_provider
from analytics import create_comparison_bar_chart

# Import tab renderers
from ui.analytics.dashboard import render_dashboard_tab
from ui.analytics.budget import render_budget_tab
from ui.analytics.periods import render_periods_tab
from ui.analytics.insights import render_insights_tab
from ui.analytics.category import render_category_tab

def render_analytics_screen():
    """Render the analytics dashboard."""
    selected_user = st.session_state.get('selected_user', '')

    # Navigation header
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Home", key="analytics_back"):
            st.session_state.current_screen = "home"
            st.rerun()
    with col_title:
        title_text = f"📊 {selected_user}'s Dashboard" if selected_user else "📊 Analytics Dashboard"
        st.markdown(f"<div class='animated-title'>{title_text}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    provider = get_data_provider()
    users = provider.get_users()

    if not users:
        st.markdown("""
        <div class='glass-card' style='text-align: center; padding: 3rem;'>
            <div style='font-size: 2rem; margin-bottom: 0.75rem;'>📭</div>
            <p style='color: var(--text-muted);'>No users found. Please create a user first!</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Create tabs for each user (+ joint if >1 user)
    tab_names = [f"{u['emoji']} {u['name']}" for u in users]
    if len(users) > 1:
        tab_names.append("👫 Joint View")

    user_tabs = st.tabs(tab_names)

    # User Tabs
    for i, user in enumerate(users):
        with user_tabs[i]:
            render_user_analytics(user['name'])

    # Joint Tab
    if len(users) > 1:
        with user_tabs[-1]:
            render_joint_analytics(users)

def render_user_analytics(user_name: str):
    """Render analytics for a specific user with view tabs."""
    user_display = user_name
    provider = get_data_provider()

    # Load transactions via provider
    data = provider.load_transactions(user_name)

    if data.empty:
        st.markdown(f"""
        <div class='glass-card' style='text-align: center; padding: 2.5rem;'>
            <div style='font-size: 2rem; margin-bottom: 0.75rem;'>📭</div>
            <p style='color: var(--text-muted);'>No data available for <strong>{user_display}</strong>. Upload some expenses first!</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # View tabs - streamlined analytics
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

def render_joint_analytics(users):
    """Render joint analytics comparing all users."""
    if len(users) < 2:
        st.info("Joint analytics requires at least 2 users.")
        return

    provider = get_data_provider()
    all_user_data = provider.get_all_users_transactions()

    if not all_user_data:
        st.info("No data available.")
        return

    # Filter/Match loaded data to current users
    active_data = {}
    for user in users:
        name = user['name']
        if name in all_user_data:
            active_data[name] = all_user_data[name]
        elif name.lower() in all_user_data:
            active_data[name] = all_user_data[name.lower()]
        elif name.lower().replace(' ', '_') in all_user_data:
             active_data[name] = all_user_data[name.lower().replace(' ', '_')]

    if not active_data:
         st.info("No matching data found for current users.")
         return

    # Summary comparison
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)

    # Dynamic columns for users
    cols = st.columns(len(active_data))
    colors = ['#FF6B9D', '#4ECDC4', '#FFE66D', '#2ECC71', '#9B59B6']
    chart_data = []

    for i, (name, df) in enumerate(active_data.items()):
        total = df[df['Amount'] < 0]['Amount'].abs().sum() if not df.empty and 'Amount' in df.columns else 0
        color = colors[i % len(colors)]

        with cols[i]:
            st.markdown(f"""
            <div class='kpi-card' style='border-top: 3px solid {color};'>
                <div class='kpi-label'>{name} Total</div>
                <div class='kpi-value' style='color: {color};'>€{total:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        chart_data.append(df)

    st.markdown("</div>", unsafe_allow_html=True)

    # Comparison bar chart
    if len(active_data) >= 2:
        keys = list(active_data.keys())
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        try:
             fig = create_comparison_bar_chart(active_data[keys[0]], active_data[keys[1]], name1=keys[0], name2=keys[1])
             st.plotly_chart(fig, use_container_width=True)
        except Exception:
             st.warning("Comparison chart limited to 2 users or legacy format.")
        st.markdown("</div>", unsafe_allow_html=True)
