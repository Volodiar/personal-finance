"""
sheets_storage.py - Google Sheets storage for cloud deployment.

Replaces local CSV storage with Google Sheets for persistent cloud storage.
Uses gspread library with service account authentication.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
import json

# Check if gspread is available (cloud deployment)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


# Google Sheets scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def get_gspread_client():
    """Get authenticated gspread client from Streamlit secrets."""
    if not GSPREAD_AVAILABLE:
        return None
    
    try:
        # Get credentials from Streamlit secrets
        creds_dict = st.secrets.get("gcp_service_account", None)
        if not creds_dict:
            return None
        
        creds = Credentials.from_service_account_info(
            dict(creds_dict),
            scopes=SCOPES
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.warning(f"Could not connect to Google Sheets: {e}")
        return None


def get_spreadsheet():
    """Get the main spreadsheet for the app."""
    client = get_gspread_client()
    if not client:
        return None
    
    try:
        spreadsheet_url = st.secrets.get("spreadsheet_url", "")
        if spreadsheet_url:
            return client.open_by_url(spreadsheet_url)
        
        spreadsheet_name = st.secrets.get("spreadsheet_name", "Personal Finance Data")
        return client.open(spreadsheet_name)
    except Exception as e:
        st.error(f"Could not open spreadsheet: {e}")
        return None


def ensure_worksheet(spreadsheet, name: str, headers: List[str] = None):
    """Ensure a worksheet exists, create if not."""
    try:
        worksheet = spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=name, rows=1000, cols=20)
        if headers:
            worksheet.append_row(headers)
    return worksheet


def load_user_data_sheets(user: str) -> pd.DataFrame:
    """Load user transactions from Google Sheets."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return pd.DataFrame()
    
    try:
        worksheet_name = f"{user}_transactions"
        worksheet = spreadsheet.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Convert types
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        return df
    except gspread.WorksheetNotFound:
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Error loading data: {e}")
        return pd.DataFrame()


def save_transactions_sheets(user: str, df: pd.DataFrame) -> bool:
    """Save transactions to Google Sheets."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet_name = f"{user}_transactions"
        headers = ['Date', 'Concept', 'Amount', 'Category']
        
        worksheet = ensure_worksheet(spreadsheet, worksheet_name, headers)
        
        # Clear existing data (keep header)
        worksheet.clear()
        
        # Prepare data
        df_copy = df.copy()
        if 'Date' in df_copy.columns:
            df_copy['Date'] = df_copy['Date'].astype(str)
        
        # Write headers and data
        data = [headers] + df_copy[headers].fillna('').values.tolist()
        worksheet.update('A1', data)
        
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False


def add_transactions_sheets(user: str, new_df: pd.DataFrame) -> Dict:
    """Add new transactions to Google Sheets (append, avoid duplicates)."""
    existing = load_user_data_sheets(user)
    
    if existing.empty:
        save_transactions_sheets(user, new_df)
        return {'added': len(new_df), 'duplicates': 0}
    
    # Create identifier for deduplication
    def create_id(row):
        return f"{row.get('Date', '')}_{row.get('Concept', '')}_{row.get('Amount', '')}"
    
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
        save_transactions_sheets(user, combined)
    
    return {'added': len(new_rows), 'duplicates': duplicates}


def load_all_data_sheets() -> Dict[str, pd.DataFrame]:
    """Load data for all users."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return {}
    
    result = {}
    try:
        worksheets = spreadsheet.worksheets()
        for ws in worksheets:
            if ws.title.endswith('_transactions'):
                user = ws.title.replace('_transactions', '')
                result[user] = load_user_data_sheets(user)
    except Exception:
        pass
    
    return result


def save_config_sheets(config_name: str, data: dict) -> bool:
    """Save configuration data to a config worksheet."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        worksheet = ensure_worksheet(spreadsheet, 'config', ['key', 'value'])
        
        # Find or add the config
        cell = worksheet.find(config_name)
        if cell:
            worksheet.update_cell(cell.row, 2, json.dumps(data))
        else:
            worksheet.append_row([config_name, json.dumps(data)])
        
        return True
    except Exception as e:
        st.warning(f"Error saving config: {e}")
        return False


def load_config_sheets(config_name: str) -> dict:
    """Load configuration data from config worksheet."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return {}
    
    try:
        worksheet = spreadsheet.worksheet('config')
        cell = worksheet.find(config_name)
        if cell:
            value = worksheet.cell(cell.row, 2).value
            return json.loads(value) if value else {}
    except Exception:
        pass
    
    return {}


# Cloud mode detection
def is_cloud_mode() -> bool:
    """Check if running in cloud mode (has Google Sheets config)."""
    try:
        return bool(st.secrets.get("gcp_service_account"))
    except Exception:
        return False
