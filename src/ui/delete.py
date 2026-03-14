import streamlit as st
import pandas as pd
from services.factory import get_data_provider


def render_delete_screen():
    """Render the transaction management / delete screen."""

    # Back navigation
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Home", key="delete_back"):
            st.session_state.current_screen = "home"
            st.rerun()
    with col_title:
        st.markdown("<div class='animated-title'>🗑️ Manage Transactions</div>", unsafe_allow_html=True)

    provider = get_data_provider()
    users = provider.get_users()

    if not users:
        st.info("No user profiles found. Create a profile first!")
        return

    user_names = [u['name'] for u in users]
    selected_user = st.selectbox("👤 Select profile", user_names, key="delete_user_select")

    if not selected_user:
        return

    # Load data
    data = provider.load_transactions(selected_user)

    if data.empty:
        st.markdown(
            "<div class='glass-card' style='text-align:center; padding: 2rem;'>"
            "<div style='font-size:2rem;'>📭</div>"
            "<p style='color:rgba(255,255,255,0.6); margin-top:0.5rem;'>No transactions found for this profile.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<p style='color:rgba(255,255,255,0.6);'>Showing <b>{len(data)}</b> transactions for <b>{selected_user}</b>. "
        f"Check the rows you want to delete, then click <em>Delete Selected</em>.</p>",
        unsafe_allow_html=True,
    )

    # Prepare display df
    display = data.copy().reset_index(drop=True)

    # Date display column
    if 'Date' in display.columns:
        display['Date'] = pd.to_datetime(display['Date'], errors='coerce')
        display['DateDisplay'] = display['Date'].apply(
            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
        )
    else:
        display['DateDisplay'] = ''

    concept_col = 'Concept' if 'Concept' in display.columns else 'Concepto' if 'Concepto' in display.columns else None
    show_cols = ['DateDisplay'] + ([concept_col] if concept_col else []) + ['Amount', 'Category']
    show_cols = [c for c in show_cols if c in display.columns]

    display_for_editor = display[show_cols].copy().rename(columns={'DateDisplay': 'Date'})
    display_for_editor.insert(0, 'Delete', False)

    # Editable table with checkboxes
    edited = st.data_editor(
        display_for_editor,
        column_config={
            "Delete": st.column_config.CheckboxColumn("🗑", default=False, width="small"),
            "Date": st.column_config.TextColumn("Date", disabled=True, width="small"),
            "Concept": st.column_config.TextColumn("Concept", disabled=True, width="large"),
            "Concepto": st.column_config.TextColumn("Concept", disabled=True, width="large"),
            "Amount": st.column_config.NumberColumn("Amount (€)", format="€%.2f", disabled=True),
            "Category": st.column_config.TextColumn("Category", disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key=f"delete_editor_{selected_user}",
    )

    selected_count = int(edited['Delete'].sum())

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    col_del, col_all, col_spacer = st.columns([2, 2, 4])

    # --- Delete Selected ---
    with col_del:
        del_btn_label = f"🗑️ Delete {selected_count} selected" if selected_count > 0 else "🗑️ Delete Selected"
        if st.button(del_btn_label, type="primary", disabled=(selected_count == 0), use_container_width=True, key="btn_del_selected"):
            keep_mask = ~edited['Delete'].values
            remaining = data.reset_index(drop=True)[keep_mask]
            provider.save_transactions(selected_user, remaining)
            st.success(f"✅ {selected_count} transaction(s) deleted.")
            st.rerun()

    # --- Delete All ---
    with col_all:
        if st.button("💥 Delete ALL", use_container_width=True, key="btn_del_all"):
            st.session_state[f"confirm_delete_all_{selected_user}"] = True

    # Confirmation step for Delete All
    if st.session_state.get(f"confirm_delete_all_{selected_user}", False):
        st.markdown(
            "<div class='glass-card' style='border-left: 3px solid #FF6B6B; padding: 1rem 1.5rem; margin-top: 0.5rem;'>"
            f"<b>⚠️ This will permanently delete ALL {len(data)} transactions for {selected_user}.</b>"
            "</div>",
            unsafe_allow_html=True,
        )
        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if st.button("✅ Yes, delete everything", type="primary", use_container_width=True, key="confirm_yes"):
                empty_df = pd.DataFrame(columns=['Date', 'Concept', 'Amount', 'Category'])
                provider.save_transactions(selected_user, empty_df)
                st.session_state.pop(f"confirm_delete_all_{selected_user}", None)
                st.success(f"✅ All transactions for {selected_user} have been deleted.")
                st.rerun()
        with conf_col2:
            if st.button("❌ Cancel", use_container_width=True, key="confirm_no"):
                st.session_state.pop(f"confirm_delete_all_{selected_user}", None)
                st.rerun()
