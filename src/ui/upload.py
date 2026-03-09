import streamlit as st
import pandas as pd
from services.factory import get_data_provider
from data_processor import parse_bank_file, process_dataframe

def render_upload_screen():
    """Render the upload and validation screen."""
    st.markdown("<h2>📤 Upload Bank Statement</h2>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your bank statement",
        type=['csv', 'pdf', 'xlsx', 'xls'],
        help="Supported: CSV (semicolon-separated), PDF (Trade Republic), Excel"
    )

    if uploaded_file:
        try:
            with st.spinner("Parsing bank statement..."):
                raw_df = parse_bank_file(uploaded_file)

            if raw_df.empty:
                st.error("Could not parse file. Please check the format.")
                return

            with st.spinner("Processing transactions..."):
                learned = st.session_state.get('learned_mappings', {})
                processed_df = process_dataframe(raw_df, learned)

            st.success(f"Found {len(processed_df)} transactions!")

            # Show preview
            st.markdown("### Preview")
            preview_cols = ['Date', 'Concepto', 'Amount', 'Category']
            available_cols = [c for c in preview_cols if c in processed_df.columns]
            st.dataframe(processed_df[available_cols].head(10), use_container_width=True)

            with st.form("upload_form"):
                provider = get_data_provider()
                users = provider.get_users()
                user_names = [u['name'] for u in users]

                if not user_names:
                    st.warning("No profiles found. Create a profile first!")
                    st.form_submit_button("Save", disabled=True)
                    return

                target_user = st.selectbox("Save to Profile", user_names)

                if st.form_submit_button("💾 Save Transactions"):
                    save_df = processed_df.copy()
                    if 'Concepto' in save_df.columns:
                        save_df = save_df.rename(columns={'Concepto': 'Concept'})
                    storage_cols = ['Date', 'Concept', 'Amount', 'Category']
                    save_df = save_df[[c for c in storage_cols if c in save_df.columns]]

                    new_count, dup_count, updated_count = provider.add_transactions(target_user, save_df)

                    st.session_state['last_upload_stats'] = (new_count, dup_count, updated_count)
                    st.session_state['current_screen'] = 'success'
                    st.rerun()

        except Exception as e:
            import traceback
            st.error(f"Error processing file: {e}")
            st.code(traceback.format_exc())

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
