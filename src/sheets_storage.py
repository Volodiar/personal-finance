"""
sheets_storage.py - Google Sheets storage for multi-tenant architecture.

Handles data storage with account-scoped worksheets using hash-based naming.
Worksheet format: {account_hash}_{data_user_id}
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import json

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


@st.cache_resource(show_spinner=False)
def get_gspread_client():
    """Get authenticated gspread client. Cached for the lifetime of the server process."""
    if not GSPREAD_AVAILABLE:
        return None
    try:
        creds_dict = st.secrets.get("gcp_service_account", None)
        if not creds_dict:
            return None
        creds = Credentials.from_service_account_info(dict(creds_dict), scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    """Get the main spreadsheet. Cached for the lifetime of the server process."""
    client = get_gspread_client()
    if not client:
        return None
    try:
        url = st.secrets.get("spreadsheet_url", "")
        if url:
            return client.open_by_url(url)
        return client.open("Personal Finance Data")
    except Exception as e:
        st.error(f"Could not open spreadsheet: {e}")
        return None


def clear_sheets_cache():
    """Invalidate all cached read data (call after any write operation)."""
    load_data_user_transactions.clear()
    load_account_mappings.clear()
    load_all_data_users_transactions.clear()


def get_worksheet_name(account_hash: str, data_user_id: str) -> str:
    """Generate worksheet name for a data user."""
    return f"{account_hash}_{data_user_id}"


def ensure_worksheet(spreadsheet, name: str, headers: List[str] = None):
    """Ensure a worksheet exists, create if not."""
    try:
        return spreadsheet.worksheet(name)
    except:
        ws = spreadsheet.add_worksheet(title=name, rows=10000, cols=10)
        if headers:
            ws.append_row(headers)
        return ws


@st.cache_data(ttl=60, show_spinner=False) # Reduced TTL to 1min for better responsiveness during fixes
def load_data_user_transactions(account_hash: str, data_user_id: str) -> pd.DataFrame:
    """
    Load transactions for a specific data user. Results cached for 5 minutes.
    """
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return pd.DataFrame()

    try:
        worksheet_name = get_worksheet_name(account_hash, data_user_id)
        ws = spreadsheet.worksheet(worksheet_name)
        # UNFORMATTED_VALUE returns the raw stored number (e.g. 15.15 as float),
        # bypassing locale-based formatting that renders it as the string '15,15' in
        # Spanish-locale Google Sheets and silently breaks pd.to_numeric.
        data = ws.get_all_records(value_render_option='UNFORMATTED_VALUE')

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Normalize column name for consistency with data_processor output
        if 'Concept' in df.columns and 'Concepto' not in df.columns:
            df = df.rename(columns={'Concept': 'Concepto'})

        if 'Amount' in df.columns:
            # Explicitly convert to float and then numeric to handle any weirdness
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').astype(float)
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        return df
    except Exception:
        return pd.DataFrame()


def save_data_user_transactions(account_hash: str, data_user_id: str, df: pd.DataFrame) -> bool:
    """
    Save transactions for a data user (overwrites existing).
    """
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        st.error("Could not get spreadsheet!")
        return False
    
    try:
        worksheet_name = get_worksheet_name(account_hash, data_user_id)
        headers = ['Date', 'Concept', 'Amount', 'Category']
        
        ws = ensure_worksheet(spreadsheet, worksheet_name, headers)
        ws.clear()
        
        df_copy = df.copy()
        if 'Date' in df_copy.columns:
            df_copy['Date'] = df_copy['Date'].astype(str)
        
        # Ensure we have all columns
        for col in headers:
            if col not in df_copy.columns:
                df_copy[col] = ''
        
        data = [headers] + df_copy[headers].fillna('').values.tolist()
        
        ws.update(values=data, range_name='A1', value_input_option='RAW')
        
        # Invalidate stale cached reads for this user
        clear_sheets_cache()
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        import traceback
        st.code(traceback.format_exc())
        return False


def add_transactions(account_hash: str, data_user_id: str, new_df: pd.DataFrame) -> Dict:
    """
    Add new transactions (merge with existing, avoid duplicates).
    
    Returns:
        Dict with 'added' and 'duplicates' counts
    """
    existing = load_data_user_transactions(account_hash, data_user_id)
    
    if existing.empty:
        success = save_data_user_transactions(account_hash, data_user_id, new_df)
        if not success:
            return {'added': 0, 'duplicates': 0, 'error': 'Failed to save to new worksheet'}
        return {'added': len(new_df), 'duplicates': 0}
    
    def create_id(row):
        date = str(row.get('Date', ''))[:10]
        concept = str(row.get('Concept', row.get('Concepto', ''))).strip().lower()
        amount = f"{float(row.get('Amount', 0)):.2f}"
        return f"{date}|{concept}|{amount}"
    
    existing_ids = set(existing.apply(create_id, axis=1))
    
    new_rows = []
    duplicates = 0
    
    for _, row in new_df.iterrows():
        if create_id(row) not in existing_ids:
            new_rows.append(row)
        else:
            duplicates += 1
    
    if new_rows:
        combined = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)
        success = save_data_user_transactions(account_hash, data_user_id, combined)
        if not success:
            return {'added': 0, 'duplicates': 0, 'error': 'Failed to save merged transactions'}
    
    return {'added': len(new_rows), 'duplicates': duplicates}


@st.cache_data(ttl=60, show_spinner=False)
def load_all_data_users_transactions(account_hash: str, data_users: tuple) -> Dict[str, pd.DataFrame]:
    """
    Load transactions for all data users of an account (for joint view).
    
    Args:
        account_hash: The account's hash
        data_users: List of data user dicts with 'id' field
        
    Returns:
        Dict mapping data_user_id to DataFrame
    """
    result = {}
    for du_tuple in data_users:
        # data_users is tuple of tuple-pairs for hashability; convert back to dict
        du = dict(du_tuple) if isinstance(du_tuple, tuple) else du_tuple
        data_user_id = du.get('id', du.get('name', '').lower())
        df = load_data_user_transactions(account_hash, data_user_id)
        if not df.empty:
            result[du.get('name', data_user_id)] = df
    return result


@st.cache_data(ttl=60, show_spinner=False)
def load_account_mappings(account_hash: str) -> dict:
    """
    Load learned category mappings for an account from Google Sheets.
    
    Args:
        account_hash: The unique hash identifying the account
        
    Returns:
        Dict of concept -> category pairs
    """
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return {}
        
    try:
        worksheet_name = f"{account_hash}_mappings"
        ws = spreadsheet.worksheet(worksheet_name)
        data = ws.get_all_records(value_render_option='UNFORMATTED_VALUE')
        
        mappings = {}
        for row in data:
            concept = str(row.get('Concept', '')).strip()
            category = str(row.get('Category', '')).strip()
            if concept and category:
                mappings[concept] = category
                
        return mappings
    except Exception:
        # Worksheet might not exist yet
        return {}


def save_account_mappings(account_hash: str, mappings: dict) -> bool:
    """
    Save learned category mappings for an account to Google Sheets.
    
    Args:
        account_hash: The unique hash identifying the account
        mappings: Dict of concept -> category pairs
        
    Returns:
        True if successful, False otherwise
    """
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
        
    try:
        worksheet_name = f"{account_hash}_mappings"
        headers = ['Concept', 'Category']
        
        ws = ensure_worksheet(spreadsheet, worksheet_name, headers)
        ws.clear()
        
        data = [headers]
        for concept, category in mappings.items():
            data.append([concept, category])
            
        ws.update(values=data, range_name='A1', value_input_option='RAW')
        clear_sheets_cache()
        return True
    except Exception as e:
        st.error(f"Error saving mappings to Sheets: {e}")
        return False


def is_cloud_mode() -> bool:
    """Check if running in cloud mode with Google Sheets."""
    try:
        return bool(st.secrets.get("gcp_service_account"))
    except:
        return False
