import streamlit as st
import pandas as pd
from services.factory import get_data_provider
from data_processor import parse_bank_file, process_dataframe
from categories import ALL_CATEGORIES
from storage import load_learned_mappings, update_learned_mappings


def render_upload_screen():
    """Render the upload and validation screen with a mandatory category review step."""
    st.markdown("<h2>📤 Upload Bank Statement</h2>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your bank statement",
        type=['csv', 'pdf', 'xlsx', 'xls'],
        help="Supported: CSV (semicolon-separated), PDF (Trade Republic), Excel"
    )

    if not uploaded_file:
        return

    # --- STEP 1: Parse & process the file ---
    try:
        with st.spinner("Parsing bank statement..."):
            raw_df = parse_bank_file(uploaded_file)

        if raw_df.empty:
            st.error("Could not parse file. Please check the format.")
            return

        with st.spinner("Processing transactions..."):
            learned = load_learned_mappings()
            processed_df = process_dataframe(raw_df, learned)

    except Exception as e:
        import traceback
        st.error(f"Error processing file: {e}")
        st.code(traceback.format_exc())
        return

    st.success(f"✅ Found **{len(processed_df)}** transactions!")

    # --- STEP 2: Category review for uncategorized transactions ---
    needs_cat_mask = (
        processed_df['Category'].isnull() |
        (processed_df['Category'] == 'Others') |
        (processed_df['Category'] == '') |
        (processed_df['Category'] == 'None')
    )
    uncategorized = processed_df[needs_cat_mask].copy()

    # Store assigned categories in session_state so they survive reruns
    ss_key = f"upload_cats_{uploaded_file.name}"
    if ss_key not in st.session_state:
        st.session_state[ss_key] = {}

    if not uncategorized.empty:
        st.markdown(
            f"<div class='glass-card' style='border-left: 3px solid #FFE66D; padding: 1rem 1.5rem;'>"
            f"<h4 style='margin:0 0 0.5rem;'>⚠️ {len(uncategorized)} transactions need a category</h4>"
            f"<p style='color:rgba(255,255,255,0.6); margin:0;'>Assign categories below — these will be remembered for future uploads.</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        for idx, row in uncategorized.iterrows():
            concept = str(row.get('Concepto', row.get('Concept', '')))
            amount = row.get('Amount', 0)
            amount_color = '#FF6B6B' if amount < 0 else '#2ECC71'
            amount_display = f"€{amount:,.2f}"

            col_concept, col_amount, col_cat = st.columns([4, 1.5, 2.5])
            with col_concept:
                st.markdown(
                    f"<div style='padding: 0.4rem 0; font-size: 0.9rem;'>{concept[:60]}</div>",
                    unsafe_allow_html=True
                )
            with col_amount:
                st.markdown(
                    f"<div style='padding: 0.4rem 0; font-size: 0.9rem; color: {amount_color};'>{amount_display}</div>",
                    unsafe_allow_html=True
                )
            with col_cat:
                current = st.session_state[ss_key].get(idx, 'Others')
                chosen = st.selectbox(
                    "Category",
                    ALL_CATEGORIES,
                    index=ALL_CATEGORIES.index(current) if current in ALL_CATEGORIES else ALL_CATEGORIES.index('Others'),
                    key=f"cat_{ss_key}_{idx}",
                    label_visibility="collapsed"
                )
                st.session_state[ss_key][idx] = chosen

    # --- STEP 3: Preview (first 10 rows) ---
    with st.expander("📋 Preview (first 10 rows)", expanded=False):
        preview_cols = ['Date', 'Concepto', 'Amount', 'Category']
        available_cols = [c for c in preview_cols if c in processed_df.columns]
        st.dataframe(processed_df[available_cols].head(10), use_container_width=True)

    # --- STEP 4: Save form ---
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    with st.form("upload_form"):
        provider = get_data_provider()
        users = provider.get_users()
        user_names = [u['name'] for u in users]

        if not user_names:
            st.warning("No profiles found. Create a profile first!")
            st.form_submit_button("Save", disabled=True)
            return

        target_user = st.selectbox("💾 Save to Profile", user_names)

        if st.form_submit_button("💾 Save Transactions", type="primary"):
            # Apply user-assigned categories to processed_df
            assigned = st.session_state.get(ss_key, {})
            new_mappings = {}
            for idx, cat in assigned.items():
                if idx in processed_df.index:
                    processed_df.at[idx, 'Category'] = cat
                    concept = str(processed_df.at[idx, 'Concepto'] if 'Concepto' in processed_df.columns else processed_df.at[idx, 'Concept'])
                    if cat and cat != 'Others':
                        new_mappings[concept] = cat

            # Persist new learned mappings
            if new_mappings:
                update_learned_mappings(new_mappings)

            # Prepare save df
            save_df = processed_df.copy()
            if 'Concepto' in save_df.columns:
                save_df = save_df.rename(columns={'Concepto': 'Concept'})
            storage_cols = ['Date', 'Concept', 'Amount', 'Category']
            save_df = save_df[[c for c in storage_cols if c in save_df.columns]]

            new_count, dup_count, updated_count = provider.add_transactions(target_user, save_df)

            # Clean up session state
            if ss_key in st.session_state:
                del st.session_state[ss_key]

            st.session_state['last_upload_stats'] = (new_count, dup_count, updated_count)
            st.session_state['current_screen'] = 'success'
            st.rerun()


def render_save_success_screen():
    """Display success stats."""
    if 'last_upload_stats' not in st.session_state:
        st.info("No recent upload.")
        return

    new, dup, updated = st.session_state['last_upload_stats']
    st.balloons()
    st.markdown(f"""
    <div class='glass-card' style='text-align: center;'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>✅</div>
        <h2>Import Successful!</h2>
        <p><strong>{new}</strong> new transactions added</p>
        <p><strong>{dup}</strong> duplicates skipped</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Back to Home", use_container_width=True):
            del st.session_state['last_upload_stats']
            st.session_state['current_screen'] = 'home'
            st.rerun()
    with col2:
        if st.button("📊 View Analytics", use_container_width=True):
            del st.session_state['last_upload_stats']
            st.session_state['current_screen'] = 'analytics'
            st.rerun()
