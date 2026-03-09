import streamlit as st
import pandas as pd
from typing import Optional
from services.factory import get_data_provider

def render_home_screen():
    """Render the home/landing screen with data user management."""
    user_name = st.session_state.get('user_name', 'there')
    user_picture = st.session_state.get('user_picture', '')

    # Welcome header with profile picture
    pic_html = ""
    if user_picture:
        pic_html = f"<img src='{user_picture}' style='width: 56px; height: 56px; border-radius: 50%; border: 2px solid var(--accent-primary); margin-bottom: 0.75rem;'>"

    first_name = user_name.split()[0] if user_name else 'there'
    st.markdown(f"""
    <div style='text-align: center; padding: 2rem 0 1rem;'>
        {pic_html}
        <h1 style='font-size: 1.8rem; margin-bottom: 0.25rem !important;'>Welcome back, {first_name}! 👋</h1>
        <p style='color: var(--text-muted); margin-bottom: 0;'>Select a profile to view your financial dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    provider = get_data_provider()
    users = provider.get_users()

    if not users:
        st.markdown("""
        <div class='glass-card' style='text-align: center; padding: 3rem;'>
            <div style='font-size: 2.5rem; margin-bottom: 1rem;'>📂</div>
            <h3 style='margin-bottom: 0.5rem;'>No profiles yet</h3>
            <p style='color: var(--text-muted);'>Create your first profile to start tracking finances.</p>
        </div>
        """, unsafe_allow_html=True)

    # Profile cards grid
    if users:
        colors = ['#4ECDC4', '#FF6B9D', '#FFE66D', '#2ECC71', '#9B59B6', '#3498DB']
        cols = st.columns(min(len(users), 4))
        for i, user in enumerate(users):
            color = colors[i % len(colors)]
            with cols[i % len(cols)]:
                st.markdown(f"""
                <div class='user-card'>
                    <span class='card-emoji'>{user['emoji']}</span>
                    <span class='card-name'>{user['name']}</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"View {user['name']}", key=f"user_btn_{i}", use_container_width=True):
                    st.session_state['selected_user'] = user['name']
                    st.session_state['current_screen'] = 'analytics'
                    st.rerun()

    # Quick actions row
    if users:
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        act_cols = st.columns(2)
        with act_cols[0]:
            st.markdown("""
            <div class='glass-card' style='text-align: center; padding: 1.25rem;'>
                <span style='font-size: 1.5rem;'>📤</span>
                <p style='margin: 0.4rem 0 0; font-weight: 500; color: var(--text-primary); font-size: 0.95rem;'>Upload Data</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Upload", key="quick_upload", use_container_width=True):
                st.session_state['current_screen'] = 'upload'
                st.rerun()
        with act_cols[1]:
            st.markdown("""
            <div class='glass-card' style='text-align: center; padding: 1.25rem;'>
                <span style='font-size: 1.5rem;'>📊</span>
                <p style='margin: 0.4rem 0 0; font-weight: 500; color: var(--text-primary); font-size: 0.95rem;'>Analytics</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Analytics", key="quick_analytics", use_container_width=True):
                st.session_state['current_screen'] = 'analytics'
                st.rerun()

    # Create New Profile section
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='glass-card' style='padding: 1.25rem 1.75rem;'>
        <h3 style='margin-bottom: 0.5rem; font-size: 1.1rem;'>➕ Create New Profile</h3>
        <p style='color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0;'>Add a new person to track their finances separately.</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("new_user_form"):
        form_cols = st.columns([3, 1])
        with form_cols[0]:
            new_name = st.text_input("Name", placeholder="Enter name...")
        with form_cols[1]:
            new_emoji = st.selectbox("Avatar", ["👤", "👩", "👨", "🚀", "💰", "🏠"])
        if st.form_submit_button("Create Profile", use_container_width=True):
            if new_name:
                if provider.add_user(new_name, new_emoji):
                    st.success(f"Created profile for {new_name}!")
                    st.rerun()
                else:
                    st.error("Profile already exists or could not be created.")
            else:
                st.warning("Please enter a name.")

def render_user_home(user_name: str):
    """Render home screen for a specific user profile."""
    st.markdown(f"## Hello, {user_name}! 👋")
    st.info(f"You are viewing data for {user_name}. Use the sidebar to navigate.")
