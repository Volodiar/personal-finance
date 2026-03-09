import streamlit as st
import pandas as pd
from categories import ALL_CATEGORIES
from services.factory import get_data_provider

def render_transaction_explorer(data: pd.DataFrame, user_display: str):
    """Render a searchable, filterable, editable transaction explorer with row selection."""
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📋 Transaction Explorer</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: rgba(255,255,255,0.6);'>Search, filter, and edit transactions. Check rows to see sum of selected amounts.</p>", unsafe_allow_html=True)
    
    # Prepare data for display
    display_data = data.copy()
    
    # FIX: Ensure Date is datetime for sorting, but handle string conversion for display
    # If it's already mixed or string, coerce first
    if 'Date' in display_data.columns:
        display_data['Date'] = pd.to_datetime(display_data['Date'], errors='coerce')
    
    # Filter controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search = st.text_input("🔍 Search", placeholder="Search concept...", key=f"search_{user_display}")
    
    with col2:
        categories = (['All'] + sorted(display_data['Category'].dropna().unique().tolist())) if 'Category' in display_data.columns else ['All']
        selected_category = st.selectbox("Category", categories, key=f"filter_cat_{user_display}")
    
    with col3:
        type_options = ['All', 'Expenses Only', 'Income Only']
        selected_type = st.selectbox("Type", type_options, key=f"filter_type_{user_display}")
    
    with col4:
        sort_options = ['Date (Newest)', 'Date (Oldest)', 'Amount (High→Low)', 'Amount (Low→High)', 'Category']
        selected_sort = st.selectbox("Sort by", sort_options, key=f"sort_{user_display}")
    
    # Apply filters
    filtered = display_data.copy()
    
    if search:
        filtered = filtered[filtered['Concepto'].str.contains(search, case=False, na=False)]
    
    if selected_category != 'All':
        filtered = filtered[filtered['Category'] == selected_category]
    
    if selected_type == 'Expenses Only':
        filtered = filtered[filtered['Amount'] < 0]
    elif selected_type == 'Income Only':
        filtered = filtered[filtered['Amount'] > 0]
    
    # Sort
    if selected_sort == 'Date (Newest)':
        filtered = filtered.sort_values('Date', ascending=False)
    elif selected_sort == 'Date (Oldest)':
        filtered = filtered.sort_values('Date', ascending=True)
    elif selected_sort == 'Amount (High→Low)':
        filtered = filtered.sort_values('Amount', ascending=False)
    elif selected_sort == 'Amount (Low→High)':
        filtered = filtered.sort_values('Amount', ascending=True)
    elif selected_sort == 'Category':
        filtered = filtered.sort_values('Category', ascending=True)
    
    # Prepare display columns
    if 'Date' in filtered.columns:
        filtered['DateDisplay'] = filtered['Date'].apply(
            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
        )
    else:
        filtered['DateDisplay'] = ''
    
    # Add Select column for row selection
    display_df = filtered[['DateDisplay', 'Concepto', 'Amount', 'Category']].copy().reset_index(drop=True)
    display_df = display_df.rename(columns={'DateDisplay': 'Date'})
    display_df.insert(0, 'Select', False)  # Add checkbox column at start
    
    # Show count
    st.markdown(f"<p style='color: rgba(255,255,255,0.6);'>Showing <b>{len(display_df)}</b> of {len(data)} transactions. Check rows to sum amounts.</p>", 
                unsafe_allow_html=True)
    
    # Editable dataframe with selection
    edited_df = st.data_editor(
        display_df,
        column_config={
            "Select": st.column_config.CheckboxColumn("✓", default=False, width="small"),
            "Date": st.column_config.TextColumn("Date", disabled=True, width="small"),
            "Concepto": st.column_config.TextColumn("Concept", disabled=True, width="large"),
            "Amount": st.column_config.NumberColumn("Amount (€)", format="€%.2f", disabled=True),
            "Category": st.column_config.SelectboxColumn("Category", options=ALL_CATEGORIES, required=True, width="medium")
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key=f"tx_explorer_{user_display}"
    )
    
    # Calculate and display sum of selected rows
    selected_rows = edited_df[edited_df['Select'] == True]
    if not selected_rows.empty:
        selected_sum = selected_rows['Amount'].sum()
        selected_count = len(selected_rows)
        
        # Display sum in red at bottom right
        sum_color = '#FF6B6B' if selected_sum < 0 else '#2ECC71'
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-end; align-items: center; margin-top: 10px;'>
            <div style='background: rgba(0,0,0,0.3); padding: 12px 20px; border-radius: 8px; border: 2px solid {sum_color};'>
                <span style='color: rgba(255,255,255,0.7); margin-right: 15px;'>{selected_count} selected</span>
                <span style='color: {sum_color}; font-size: 1.4rem; font-weight: bold;'>Σ €{selected_sum:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Check for category changes and save
    original_categories = display_df['Category']
    edited_categories = edited_df['Category']
    
    if not original_categories.equals(edited_categories):
        changed_mask = original_categories != edited_categories
        if changed_mask.any():
            changes = {}
            for idx in display_df[changed_mask].index:
                concept = edited_df.loc[idx, 'Concepto']
                new_cat = edited_df.loc[idx, 'Category']
                if new_cat and new_cat != 'Others':
                    changes[concept] = new_cat
            
            if changes:
                if st.button("💾 Save Category Changes", type="primary", key=f"save_changes_{user_display}"):
                    # Modularized save logic
                    # We need to update learned mappings AND save the updated transactions to storage
                    from storage import update_learned_mappings
                    update_learned_mappings(changes)
                    
                    provider = get_data_provider()
                    # We need to reload the FULL data, apply changes, and save back
                    # This is slightly inefficient but safe. 
                    # Optimization: manipulate the 'data' passed in? No, 'data' is disconnected from storage.
                    
                    user_data = provider.load_transactions(user_display)
                    
                    # Apply changes to user_data
                    for concept, new_cat in changes.items():
                        # Update all occurrences of this concept? Or just specific rows?
                        # The explorer usually implies updating "this transaction", but the learning implies "all future".
                        # The original code did: user_data.loc[user_data['Concepto'] == concept, 'Category'] = new_cat
                        # This updates ALL transactions with that concept.
                        user_data.loc[user_data['Concepto'] == concept, 'Category'] = new_cat
                        
                    provider.save_transactions(user_display, user_data)
                    
                    st.success(f"✅ Updated {len(changes)} category mapping(s)!")
                    st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
