import streamlit as st
from auth import logout

def render_header_controls():
    """Render theme toggle, user info, and logout button in the header."""
    user_name = st.session_state.get('user_name', '')
    user_picture = st.session_state.get('user_picture', '')
    theme = st.session_state.get('theme', 'dark')
    theme_icon = "☀️" if theme == 'dark' else "🌙"

    cols = st.columns([6, 2, 1, 1])

    with cols[1]:
        if user_picture:
            st.markdown(f"""
            <div style='display: flex; align-items: center; gap: 0.5rem; justify-content: flex-end; padding-top: 0.5rem;'>
                <span style='color: var(--text-secondary); font-size: 0.85rem;'>{user_name.split()[0] if user_name else ''}</span>
                <img src='{user_picture}' style='width: 32px; height: 32px; border-radius: 50%; border: 1.5px solid var(--accent-primary);'>
            </div>
            """, unsafe_allow_html=True)
        elif user_name:
            st.markdown(f"<div style='text-align: right; padding-top: 0.75rem; color: var(--text-secondary); font-size: 0.85rem;'>{user_name.split()[0]}</div>", unsafe_allow_html=True)

    with cols[2]:
        if st.button(theme_icon, key="theme_toggle", help="Toggle Dark/Light mode"):
            st.session_state.theme = 'light' if theme == 'dark' else 'dark'
            st.rerun()

    with cols[3]:
        if st.button("↩", key="logout_btn", help="Logout"):
            logout()
