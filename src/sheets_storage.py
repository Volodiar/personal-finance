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


def get_gspread_client():
    """Get authenticated gspread client."""
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


def get_spreadsheet():
    """Get the main spreadsheet."""
    client = get_gspread_client()
    if not client:
        return None
    try:
        url = st.secrets.get("spreadsheet_url", "")
        if url:
            return client.open_by_url(url)
        return client.open("Personal Finance Data")
    except Exception:
        return None


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


def load_data_user_transactions(account_hash: str, data_user_id: str) -> pd.DataFrame:
    """
    Load transactions for a specific data user.
    
    Args:
        account_hash: The account's unique hash
        data_user_id: The data user's ID
        
    Returns:
        DataFrame with transactions
    """
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return pd.DataFrame()
    
    try:
        worksheet_name = get_worksheet_name(account_hash, data_user_id)
        ws = spreadsheet.worksheet(worksheet_name)
        data = ws.get_all_records()
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        return df
    except:
        return pd.DataFrame()


def save_data_user_transactions(account_hash: str, data_user_id: str, df: pd.DataFrame) -> bool:
    """
    Save transactions for a data user (overwrites existing).
    
    Args:
        account_hash: The account's unique hash
        data_user_id: The data user's ID
        df: DataFrame with transactions
        
    Returns:
        True if successful
    """
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
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
        ws.update('A1', data)
        
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False


def add_transactions(account_hash: str, data_user_id: str, new_df: pd.DataFrame) -> Dict:
    """
    Add new transactions (merge with existing, avoid duplicates).
    
    Returns:
        Dict with 'added' and 'duplicates' counts
    """
    existing = load_data_user_transactions(account_hash, data_user_id)
    
    if existing.empty:
        save_data_user_transactions(account_hash, data_user_id, new_df)
        return {'added': len(new_df), 'duplicates': 0}
    
    def create_id(row):
        date = str(row.get('Date', ''))[:10]
        concept = str(row.get('Concept', '')).strip().lower()
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
        save_data_user_transactions(account_hash, data_user_id, combined)
    
    return {'added': len(new_rows), 'duplicates': duplicates}


def load_all_data_users_transactions(account_hash: str, data_users: List[Dict]) -> Dict[str, pd.DataFrame]:
    """
    Load transactions for all data users of an account (for joint view).
    
    Args:
        account_hash: The account's hash
        data_users: List of data user dicts with 'id' field
        
    Returns:
        Dict mapping data_user_id to DataFrame
    """
    result = {}
    for du in data_users:
        data_user_id = du.get('id', du.get('name', '').lower())
        df = load_data_user_transactions(account_hash, data_user_id)
        if not df.empty:
            result[du.get('name', data_user_id)] = df
    return result


def is_cloud_mode() -> bool:
    """Check if running in cloud mode with Google Sheets."""
    try:
        return bool(st.secrets.get("gcp_service_account"))
    except:
        return False
