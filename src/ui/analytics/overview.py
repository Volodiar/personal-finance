import streamlit as st
import pandas as pd
from analytics import (
    calculate_kpis, create_category_pie_chart, 
    create_income_expense_trend, get_category_breakdown
)
from ui.analytics.explorer import render_transaction_explorer

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
        savings_rate = kpis.get('savings_rate', 0)
        savings_color = '#2ECC71' if savings_rate >= 20 else '#FFE66D' if savings_rate >= 0 else '#FF6B6B'
        st.markdown(f"""
        <div class='kpi-card' style='border-left: 4px solid {savings_color};'>
            <div class='kpi-label'>Savings Rate</div>
            <div class='kpi-value' style='color: {savings_color};'>{savings_rate:.1f}%</div>
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
