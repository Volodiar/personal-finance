import streamlit as st
import pandas as pd
from budgets import (
    get_user_budgets, set_category_budget, remove_category_budget,
    get_user_goals, add_goal, update_goal_progress, delete_goal,
    calculate_budget_status, calculate_goal_progress, get_budget_alerts
)
from categories import ALL_CATEGORIES

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
