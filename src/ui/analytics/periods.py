import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from analytics import (
    get_daily_summary, create_daily_chart_all,
    get_monthly_summary, create_monthly_chart,
    get_annual_summary, create_annual_chart
)
from storage import get_available_years # Using direct storage import as helper, or should abstract?
# Ideally abstract, but for now direct import is fine if we keep it clean.
# Actually, storage.get_available_years uses load_user_data internally which checks cloud mode.
# So it is safe to use if it doesn't break the new provider pattern.
# However, the provider should expose this.
# Let's check if provider expose get_available_years... no.
# We should probably adapt get_available_years to use the dataframe passed in, or use provider.
# But existing get_available_years takes a user name and loads data again. 
# We have 'data' passed to the render functions. We should just derive years from 'data' to be more efficient and consistent.

def get_years_from_data(data: pd.DataFrame) -> list:
    if data.empty or 'Date' not in data.columns:
        return []
    
    valid_dates = pd.to_datetime(data['Date'], errors='coerce').dropna()
    if valid_dates.empty:
        return []
        
    return sorted(valid_dates.dt.year.unique(), reverse=True)

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
        # Import here to avoid circular dependencies if any
        from ui.analytics.calendar import render_calendar_tab
        render_calendar_tab(data, user_display)

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
    years = get_years_from_data(data)
    
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
