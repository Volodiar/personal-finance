"""
accounts.py - Account management for multi-tenant architecture.

Manages Account Users (OAuth logins) and their Data Users (profiles for data separation).
Each account has a unique hash for worksheet naming to avoid collisions.
"""

import streamlit as st
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional

# Try to import gspread
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
    except Exception as e:
        st.warning(f"Could not connect to Google Sheets: {e}")
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
    except Exception as e:
        st.error(f"Could not open spreadsheet: {e}")
        return None


def generate_account_hash(email: str) -> str:
    """Generate a short unique hash for an account."""
    return hashlib.md5(email.lower().encode()).hexdigest()[:8]


def get_worksheet_name(account_hash: str, data_user_id: str) -> str:
    """Generate worksheet name for a data user."""
    return f"{account_hash}_{data_user_id}"


def ensure_accounts_worksheet(spreadsheet) -> Optional[object]:
    """Ensure accounts worksheet exists."""
    try:
        return spreadsheet.worksheet("accounts")
    except:
        ws = spreadsheet.add_worksheet(title="accounts", rows=1000, cols=10)
        ws.append_row(["email", "hash", "data_users", "created"])
        return ws


def get_account(email: str) -> Optional[Dict]:
    """Get account by email."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return None
    
    try:
        ws = ensure_accounts_worksheet(spreadsheet)
        records = ws.get_all_records()
        
        for record in records:
            if record.get("email", "").lower() == email.lower():
                data_users = record.get("data_users", "[]")
                if isinstance(data_users, str):
                    data_users = json.loads(data_users) if data_users else []
                return {
                    "email": record["email"],
                    "hash": record["hash"],
                    "data_users": data_users,
                    "created": record.get("created", "")
                }
        return None
    except Exception as e:
        st.warning(f"Error getting account: {e}")
        return None


def create_account(email: str) -> Dict:
    """Create a new account for an email."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return {"email": email, "hash": generate_account_hash(email), "data_users": []}
    
    try:
        ws = ensure_accounts_worksheet(spreadsheet)
        
        # Check if already exists
        existing = get_account(email)
        if existing:
            return existing
        
        # Create new account
        account_hash = generate_account_hash(email)
        new_account = {
            "email": email,
            "hash": account_hash,
            "data_users": [],
            "created": datetime.now().isoformat()
        }
        
        ws.append_row([
            email,
            account_hash,
            json.dumps([]),
            new_account["created"]
        ])
        
        return new_account
    except Exception as e:
        st.warning(f"Error creating account: {e}")
        return {"email": email, "hash": generate_account_hash(email), "data_users": []}


def get_or_create_account(email: str) -> Dict:
    """Get existing account or create new one."""
    account = get_account(email)
    if account:
        return account
    return create_account(email)


def add_data_user(email: str, name: str, emoji: str = "👤") -> bool:
    """Add a data user to an account."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        account = get_or_create_account(email)
        ws = ensure_accounts_worksheet(spreadsheet)
        
        # Generate ID from name
        data_user_id = name.lower().replace(" ", "_")
        data_user_id = "".join(c for c in data_user_id if c.isalnum() or c == "_")
        
        # Check if already exists
        for du in account["data_users"]:
            if du["id"] == data_user_id:
                return False  # Already exists
        
        # Add new data user
        new_data_user = {
            "id": data_user_id,
            "name": name,
            "emoji": emoji,
            "created": datetime.now().isoformat()
        }
        account["data_users"].append(new_data_user)
        
        # Update in sheet
        cell = ws.find(email)
        if cell:
            ws.update_cell(cell.row, 3, json.dumps(account["data_users"]))
        
        # Create worksheet for this data user
        worksheet_name = get_worksheet_name(account["hash"], data_user_id)
        try:
            spreadsheet.worksheet(worksheet_name)
        except:
            new_ws = spreadsheet.add_worksheet(title=worksheet_name, rows=10000, cols=10)
            new_ws.append_row(["Date", "Concept", "Amount", "Category"])
        
        return True
    except Exception as e:
        st.warning(f"Error adding data user: {e}")
        return False


def delete_data_user(email: str, data_user_id: str) -> bool:
    """Delete a data user from an account."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        account = get_account(email)
        if not account:
            return False
        
        ws = ensure_accounts_worksheet(spreadsheet)
        
        # Remove from list
        account["data_users"] = [du for du in account["data_users"] if du["id"] != data_user_id]
        
        # Update in sheet
        cell = ws.find(email)
        if cell:
            ws.update_cell(cell.row, 3, json.dumps(account["data_users"]))
        
        # Optionally delete the worksheet (commented for safety)
        # worksheet_name = get_worksheet_name(account["hash"], data_user_id)
        # try:
        #     ws_to_delete = spreadsheet.worksheet(worksheet_name)
        #     spreadsheet.del_worksheet(ws_to_delete)
        # except:
        #     pass
        
        return True
    except Exception as e:
        st.warning(f"Error deleting data user: {e}")
        return False


def update_data_user(email: str, data_user_id: str, new_name: str = None, new_emoji: str = None) -> bool:
    """Update a data user's name or emoji."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return False
    
    try:
        account = get_account(email)
        if not account:
            return False
        
        ws = ensure_accounts_worksheet(spreadsheet)
        
        # Update data user
        for du in account["data_users"]:
            if du["id"] == data_user_id:
                if new_name:
                    du["name"] = new_name
                if new_emoji:
                    du["emoji"] = new_emoji
                break
        
        # Update in sheet
        cell = ws.find(email)
        if cell:
            ws.update_cell(cell.row, 3, json.dumps(account["data_users"]))
        
        return True
    except Exception as e:
        st.warning(f"Error updating data user: {e}")
        return False


def get_data_users(email: str) -> List[Dict]:
    """Get all data users for an account."""
    account = get_account(email)
    if account:
        return account.get("data_users", [])
    return []


def get_account_hash(email: str) -> str:
    """Get the hash for an account (creating if needed)."""
    account = get_or_create_account(email)
    return account.get("hash", generate_account_hash(email))
