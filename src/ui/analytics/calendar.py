import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from insights import get_transaction_calendar

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
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📋 Transactions This Month</h3>", unsafe_allow_html=True)
    
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
