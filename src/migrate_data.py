"""
migrate_data.py - Migrate local CSV data to Google Sheets.

Run this script once to migrate your existing data to the new multi-tenant format.
Usage: streamlit run src/migrate_data.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

st.set_page_config(page_title="Data Migration", page_icon="🔄", layout="wide")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from accounts import get_or_create_account, add_data_user, get_account_hash, get_worksheet_name
from sheets_storage import save_data_user_transactions, load_data_user_transactions, is_cloud_mode

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"


def main():
    st.title("🔄 Data Migration Tool")
    st.markdown("Migrate your local CSV data to Google Sheets")
    
    # Check cloud mode
    if not is_cloud_mode():
        st.error("⚠️ Google Sheets not configured. Add gcp_service_account to secrets.")
        st.info("This tool requires cloud mode to be enabled.")
        return
    
    st.success("✅ Connected to Google Sheets")
    
    # Step 1: Enter your email
    st.markdown("### Step 1: Your Account Email")
    email = st.text_input("Enter your Google email (the one you'll use to log in):", 
                          placeholder="pablo@gmail.com")
    
    if not email:
        st.info("Enter your email to continue")
        return
    
    # Create/get account
    account = get_or_create_account(email)
    st.markdown(f"**Account hash:** `{account['hash']}`")
    
    # Step 2: Detect local data
    st.markdown("### Step 2: Detected Local Data")
    
    local_data = {}
    if DATA_DIR.exists():
        for folder in DATA_DIR.iterdir():
            if folder.is_dir():
                csv_file = folder / "transactions.csv"
                if csv_file.exists():
                    try:
                        df = pd.read_csv(csv_file)
                        local_data[folder.name] = {
                            "path": csv_file,
                            "rows": len(df),
                            "df": df
                        }
                    except Exception as e:
                        st.warning(f"Could not read {csv_file}: {e}")
    
    if not local_data:
        st.info("No local CSV data found in /data/ folders")
        return
    
    # Show detected data
    for name, info in local_data.items():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"📁 **{name}**")
        with col2:
            st.markdown(f"{info['rows']} transactions")
        with col3:
            st.markdown(f"`{info['path'].name}`")
    
    # Step 3: Map to data users
    st.markdown("### Step 3: Configure Data Users")
    st.markdown("Each folder will become a data user in your account.")
    
    data_user_config = {}
    for folder_name in local_data.keys():
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            name = st.text_input(f"Display name for '{folder_name}':", 
                                value=folder_name.capitalize(),
                                key=f"name_{folder_name}")
        with col2:
            emoji = st.selectbox(f"Emoji:", 
                                ["👤", "👩", "👨", "👧", "👦", "👨‍👩‍👧‍👦", "💼", "🏠"],
                                key=f"emoji_{folder_name}")
        with col3:
            migrate = st.checkbox("Migrate", value=True, key=f"migrate_{folder_name}")
        
        if migrate:
            data_user_config[folder_name] = {
                "name": name,
                "emoji": emoji,
                "id": folder_name.lower().replace(" ", "_")
            }
    
    if not data_user_config:
        st.warning("Select at least one folder to migrate")
        return
    
    # Step 4: Preview
    st.markdown("### Step 4: Preview")
    
    st.markdown("**Will create:**")
    for folder_name, config in data_user_config.items():
        worksheet_name = get_worksheet_name(account['hash'], config['id'])
        rows = local_data[folder_name]['rows']
        st.markdown(f"- {config['emoji']} **{config['name']}** → worksheet `{worksheet_name}` ({rows} rows)")
    
    # Step 5: Migrate
    st.markdown("### Step 5: Migrate")
    
    if st.button("🚀 Start Migration", type="primary"):
        progress = st.progress(0)
        status = st.empty()
        
        total = len(data_user_config)
        for i, (folder_name, config) in enumerate(data_user_config.items()):
            status.markdown(f"Migrating **{config['name']}**...")
            
            # Add data user to account
            add_data_user(email, config['name'], config['emoji'])
            
            # Get data - make a copy!
            df = local_data[folder_name]['df'].copy()
            
            # Debug: show original columns
            st.write(f"Original columns: {list(df.columns)}")
            
            # Normalize columns
            column_mapping = {
                'Concepto': 'Concept',
                'concepto': 'Concept',
            }
            df = df.rename(columns=column_mapping)
            
            # Debug: show renamed columns
            st.write(f"After rename: {list(df.columns)}")
            
            # Ensure required columns
            if 'Date' not in df.columns:
                for col in df.columns:
                    if 'date' in col.lower() or 'fecha' in col.lower():
                        df['Date'] = df[col]
                        break
            
            if 'Amount' not in df.columns:
                for col in df.columns:
                    if 'amount' in col.lower() or 'importe' in col.lower():
                        df['Amount'] = df[col]
                        break
            
            if 'Category' not in df.columns:
                df['Category'] = ''
            
            # Debug: show final columns and sample
            st.write(f"Final columns: {list(df.columns)}")
            st.write(f"Sample row: {df[['Date', 'Concept', 'Amount', 'Category']].head(1).to_dict()}")
            
            # Save to sheets
            success = save_data_user_transactions(account['hash'], config['id'], df)
            
            if success:
                st.success(f"✅ {config['name']}: {len(df)} rows migrated")
            else:
                st.error(f"❌ {config['name']}: Migration failed")
            
            progress.progress((i + 1) / total)
        
        status.markdown("**Migration complete!**")
        st.balloons()
        
        # Verify
        st.markdown("### Verification")
        for folder_name, config in data_user_config.items():
            loaded = load_data_user_transactions(account['hash'], config['id'])
            original_rows = local_data[folder_name]['rows']
            loaded_rows = len(loaded)
            
            if loaded_rows >= original_rows:
                st.success(f"✅ {config['name']}: {loaded_rows} rows in Sheets (expected {original_rows})")
            else:
                st.warning(f"⚠️ {config['name']}: {loaded_rows} rows in Sheets (expected {original_rows})")


if __name__ == "__main__":
    main()
