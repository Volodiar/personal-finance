import streamlit as st
import pandas as pd
from analytics import (
    calculate_kpis,
    create_category_pie_chart, create_income_expense_trend,
    get_category_breakdown, filter_data_by_period
)
from insights import calculate_spending_velocity
from budgets import get_budget_alerts

def render_dashboard_tab(data: pd.DataFrame, user_display: str):
    """Render dashboard with quick-glance widgets."""
    user = user_display.lower()

    # Time Period Selector
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col_title, col_selector = st.columns([3, 1])
    with col_title:
        st.markdown("<h3 style='margin-bottom: 0;'>⚡ Quick Glance</h3>", unsafe_allow_html=True)
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

    if filtered_data.empty:
        st.info(f"No transactions found for {selected_period_label.split(' ', 1)[1]}. Try selecting a different time period.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Calculate KPIs with filtered data
    kpis = calculate_kpis(filtered_data)
    velocity = calculate_spending_velocity(filtered_data)

    # Income & Expenses totals
    total_income = filtered_data[filtered_data['Amount'] > 0]['Amount'].sum() if 'Amount' in filtered_data.columns else 0
    total_expenses = filtered_data[filtered_data['Amount'] < 0]['Amount'].abs().sum() if 'Amount' in filtered_data.columns else 0

    # KPI row 1: Balance, Income, Expenses
    col1, col2, col3 = st.columns(3)

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
        <div class='kpi-card' style='border-top: 3px solid #2ECC71;'>
            <div class='kpi-label'>📈 Income</div>
            <div class='kpi-value' style='color: #2ECC71;'>€{total_income:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='kpi-card' style='border-top: 3px solid #FF6B6B;'>
            <div class='kpi-label'>📉 Expenses</div>
            <div class='kpi-value' style='color: #FF6B6B;'>€{total_expenses:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # KPI row 2: Rate, Projection, Savings
    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown(f"""
        <div class='kpi-card' style='border-top: 3px solid #FF6B6B;'>
            <div class='kpi-label'>📅 Daily Rate</div>
            <div class='kpi-value' style='color: #FF6B6B;'>€{velocity['daily_rate']:.0f}/day</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class='kpi-card' style='border-top: 3px solid #FFE66D;'>
            <div class='kpi-label'>📊 Month Projection</div>
            <div class='kpi-value' style='color: #FFE66D;'>€{velocity['projected_month']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        savings_rate = kpis.get('savings_rate', 0)
        savings_color = '#2ECC71' if savings_rate >= 20 else '#FFE66D' if savings_rate >= 0 else '#FF6B6B'
        st.markdown(f"""
        <div class='kpi-card' style='border-top: 3px solid {savings_color};'>
            <div class='kpi-label'>💎 Savings Rate</div>
            <div class='kpi-value' style='color: {savings_color};'>{savings_rate:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Budget Alerts Widget
    alerts = get_budget_alerts(user, filtered_data)
    if alerts:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-bottom: 0.75rem;'>🔔 Budget Alerts</h3>", unsafe_allow_html=True)
        for alert in alerts[:3]:
            level = alert.get("level", "warning")
            alert_class = "alert-card-danger" if level == "danger" else "alert-card-warning"
            icon = "🚨" if level == "danger" else "⚠️"
            st.markdown(f"""
            <div class='alert-card {alert_class}'>
                <span>{icon}</span>
                <div><strong>{alert['category']}</strong>: {alert['message']}</div>
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
    st.markdown("<h3 style='margin-bottom: 0.75rem;'>🏷️ Top Spending Categories</h3>", unsafe_allow_html=True)
    breakdown = get_category_breakdown(filtered_data)
    if not breakdown.empty:
        breakdown = breakdown.head(5)
        breakdown['Amount'] = breakdown['Amount'].apply(lambda x: f"€{x:,.2f}")
        breakdown['Percent'] = breakdown['Percent'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(breakdown, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Transaction Explorer
    from ui.analytics.explorer import render_transaction_explorer
    render_transaction_explorer(filtered_data, user_display)
