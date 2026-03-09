import streamlit as st
import pandas as pd
from insights import (
    calculate_spending_velocity, detect_anomalies, 
    detect_recurring_transactions, get_monthly_fixed_costs
)

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
