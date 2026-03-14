import streamlit as st
import pandas as pd
from services.factory import get_data_provider
from data_processor import parse_bank_file, process_dataframe
from categories import ALL_CATEGORIES
from storage import load_learned_mappings, update_learned_mappings


def _get_file_key(uploaded_file) -> str:
    """Stable key based on filename + size — changes only when a new file is chosen."""
    return f"upload__{uploaded_file.name}__{uploaded_file.size}"


def render_upload_screen():
    """Render the upload screen with a one-time parse and deduped category review."""
    st.markdown("<h2>📤 Upload Bank Statement</h2>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your bank statement",
        type=['csv', 'pdf', 'xlsx', 'xls'],
        help="Supported: CSV (semicolon-separated), PDF (Trade Republic), Excel"
    )

    if not uploaded_file:
        # Clear stale session data when no file is selected
        for key in list(st.session_state.keys()):
            if key.startswith("upload__"):
                del st.session_state[key]
        return

    file_key = _get_file_key(uploaded_file)
    df_key = f"{file_key}__df"
    cats_key = f"{file_key}__cats"   # dict: unique_concept -> chosen_category

    # ── STEP 1: Parse & process ONCE per file ──────────────────────────────────
    # Only runs the first time for this file; subsequent selectbox changes skip this.
    if df_key not in st.session_state:
        try:
            with st.spinner("Parsing bank statement... (one moment)"):
                raw_df = parse_bank_file(uploaded_file)

            if raw_df.empty:
                st.error("Could not parse file. Please check the format.")
                return

            # Load learned mappings ONCE here — never again during this session
            with st.spinner("Applying learned categories..."):
                learned = load_learned_mappings()
                processed_df = process_dataframe(raw_df, learned)

            st.session_state[df_key] = processed_df
            st.session_state[cats_key] = {}   # will be filled below

        except Exception as e:
            import traceback
            st.error(f"Error processing file: {e}")
            st.code(traceback.format_exc())
            return

    processed_df: pd.DataFrame = st.session_state[df_key]
    assigned_cats: dict = st.session_state[cats_key]   # concept -> category (user overrides)

    st.success(f"✅ Found **{len(processed_df)}** transactions!")

    # ── STEP 2: Deduped category review  ──────────────────────────────────────
    # Identify concepts without a solid auto-category
    uncertain_mask = (
        processed_df['Category'].isnull() |
        (processed_df['Category'] == 'Others') |
        (processed_df['Category'] == '') |
        (processed_df['Category'].astype(str) == 'None')
    )
    uncategorized = processed_df[uncertain_mask].copy()

    if not uncategorized.empty:
        # Build a deduplicated list: one row per unique concept name
        concept_col = 'Concepto' if 'Concepto' in uncategorized.columns else 'Concept'
        unique_concepts = (
            uncategorized.groupby(concept_col)['Amount']
            .agg(['count', 'sum'])
            .reset_index()
            .rename(columns={concept_col: 'Concept', 'count': 'Txns', 'sum': 'Total'})
            .sort_values('Txns', ascending=False)
        )

        st.markdown(
            f"<div class='glass-card' style='border-left: 3px solid #FFE66D; padding: 1rem 1.5rem;'>"
            f"<h4 style='margin:0 0 0.5rem;'>⚠️ {len(unique_concepts)} unique concept(s) need a category</h4>"
            f"<p style='color:rgba(255,255,255,0.6); margin:0;'>"
            f"Each category applies to all transactions sharing that name. "
            f"Changes are only saved when you click <em>Save Transactions</em>.</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # Header row
        hcol1, hcol2, hcol3, hcol4 = st.columns([4, 1, 1.5, 2.5])
        hcol1.markdown("<small style='color:rgba(255,255,255,0.4)'>Concept</small>", unsafe_allow_html=True)
        hcol2.markdown("<small style='color:rgba(255,255,255,0.4)'>#</small>", unsafe_allow_html=True)
        hcol3.markdown("<small style='color:rgba(255,255,255,0.4)'>Total</small>", unsafe_allow_html=True)
        hcol4.markdown("<small style='color:rgba(255,255,255,0.4)'>Category</small>", unsafe_allow_html=True)

        for _, row in unique_concepts.iterrows():
            concept = str(row['Concept'])
            txn_count = int(row['Txns'])
            total = float(row['Total'])
            total_color = '#FF6B6B' if total < 0 else '#2ECC71'

            # Current selection (default to 'Others')
            current = assigned_cats.get(concept, 'Others')
            default_idx = ALL_CATEGORIES.index(current) if current in ALL_CATEGORIES else ALL_CATEGORIES.index('Others')

            col1, col2, col3, col4 = st.columns([4, 1, 1.5, 2.5])
            with col1:
                st.markdown(
                    f"<div style='padding:0.35rem 0; font-size:0.88rem'>{concept[:55]}</div>",
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f"<div style='padding:0.35rem 0; font-size:0.88rem; color:rgba(255,255,255,0.5)'>{txn_count}</div>",
                    unsafe_allow_html=True
                )
            with col3:
                st.markdown(
                    f"<div style='padding:0.35rem 0; font-size:0.88rem; color:{total_color}'>€{total:,.2f}</div>",
                    unsafe_allow_html=True
                )
            with col4:
                # selectbox writes to session_state — no API call triggered
                chosen = st.selectbox(
                    "cat",
                    ALL_CATEGORIES,
                    index=default_idx,
                    key=f"cat__{file_key}__{concept}",
                    label_visibility="collapsed"
                )
                # Persist choice in session_state dict without a rerender-triggered API call
                if chosen != assigned_cats.get(concept):
                    assigned_cats[concept] = chosen
                    st.session_state[cats_key] = assigned_cats

    # ── STEP 3: Preview ────────────────────────────────────────────────────────
    with st.expander("📋 Preview (first 10 rows)", expanded=False):
        preview_cols = ['Date', 'Concepto', 'Amount', 'Category']
        available = [c for c in preview_cols if c in processed_df.columns]
        st.dataframe(processed_df[available].head(10), use_container_width=True)

    # ── STEP 4: Save form ──────────────────────────────────────────────────────
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

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
            # Apply per-concept category assignments to *all* matching rows
            save_df = processed_df.copy()
            concept_col = 'Concepto' if 'Concepto' in save_df.columns else 'Concept'
            new_mappings = {}
            for concept, cat in assigned_cats.items():
                save_df.loc[save_df[concept_col] == concept, 'Category'] = cat
                if cat and cat != 'Others':
                    new_mappings[concept] = cat

            # ← This is the ONLY moment we write to Google Sheets
            if new_mappings:
                update_learned_mappings(new_mappings)

            if 'Concepto' in save_df.columns:
                save_df = save_df.rename(columns={'Concepto': 'Concept'})
            storage_cols = ['Date', 'Concept', 'Amount', 'Category']
            save_df = save_df[[c for c in storage_cols if c in save_df.columns]]

            new_count, dup_count, updated_count = provider.add_transactions(target_user, save_df)

            # Clean up session state for this file
            for key in [df_key, cats_key]:
                st.session_state.pop(key, None)

            st.session_state['last_upload_stats'] = (new_count, dup_count, updated_count)
            st.session_state['current_screen'] = 'success'
            st.rerun()


def render_save_success_screen():
    """Display success stats after upload."""
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
