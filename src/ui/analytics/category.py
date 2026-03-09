import streamlit as st
import pandas as pd
from analytics import (
    create_category_breakdown_chart, create_category_trend, get_category_summary
)

def render_category_tab(data: pd.DataFrame, user_display: str):
    """Render category view tab."""
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    # Period selector for breakdown
    period = st.radio(
        "Group by",
        ["Month", "Year"],
        horizontal=True,
        key=f"category_period_{user_display}"
    )
    period_val = period.lower()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Category breakdown chart
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    fig = create_category_breakdown_chart(data, period_val)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Category trend for selected category
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    if 'Category' in data.columns:
        categories = sorted(data['Category'].dropna().unique())
        if categories:
            selected_category = st.selectbox(
                "View trend for category",
                categories,
                key=f"category_trend_{user_display}"
            )
            
            fig = create_category_trend(data, selected_category)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Category summary table
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    summary = get_category_summary(data)
    if not summary.empty:
        st.markdown("<h4>Category Summary</h4>", unsafe_allow_html=True)
        st.dataframe(summary, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
