"""
storage.py - File I/O and learning engine persistence.

Handles directory creation, JSON config management, and CSV storage
for processed bank statements with smart merging and duplicate detection.
"""

import os
import json
import hashlib
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

# Base paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
MAPPING_FILE = CONFIG_DIR / "category_mapping.json"


def ensure_directories():
    """Create the required directory structure if it doesn't exist."""
    directories = [
        DATA_DIR / "masha",
        DATA_DIR / "pablo",
        CONFIG_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create config file if it doesn't exist
    if not MAPPING_FILE.exists():
        save_learned_mappings({})


def load_learned_mappings() -> dict:
    """
    Load learned concept-to-category mappings from JSON.
    
    Returns:
        Dict of concept -> category pairs
    """
    ensure_directories()
    
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('learned_mappings', {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_learned_mappings(mappings: dict):
    """
    Save learned mappings to JSON file.
    
    Args:
        mappings: Dict of concept -> category pairs
    """
    ensure_directories()
    
    data = {'learned_mappings': mappings}
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_learned_mappings(new_mappings: dict):
    """
    Update learned mappings with new user corrections.
    
    Args:
        new_mappings: Dict of concept -> category pairs to add/update
    """
    current = load_learned_mappings()
    current.update(new_mappings)
    save_learned_mappings(current)


def get_user_data_path(user: str) -> Path:
    """Get the data directory path for a user."""
    user_lower = user.lower()
    if user_lower not in ['masha', 'pablo']:
        raise ValueError(f"Invalid user: {user}. Must be 'masha' or 'pablo'.")
    return DATA_DIR / user_lower


def get_user_data_file(user: str) -> Path:
    """Get the consolidated transactions file path for a user."""
    return get_user_data_path(user) / "transactions.csv"


def create_transaction_id(row: pd.Series) -> str:
    """
    Create a unique identifier for a transaction based on its key fields.
    
    Uses Concepto + Date + Amount to create a hash that identifies duplicates.
    
    Args:
        row: DataFrame row with transaction data
        
    Returns:
        Hash string uniquely identifying this transaction
    """
    # Build a string from key fields
    concept = str(row.get('Concepto', '')).strip().lower()
    
    # Handle date - convert to string format
    date_val = row.get('Date', '')
    if pd.notna(date_val):
        if isinstance(date_val, datetime):
            date_str = date_val.strftime('%Y-%m-%d')
        else:
            date_str = str(date_val)[:10]  # Take first 10 chars (YYYY-MM-DD)
    else:
        date_str = ''
    
    # Handle amount
    amount = row.get('Amount', 0)
    if pd.isna(amount):
        amount = 0
    amount_str = f"{float(amount):.2f}"
    
    # Create hash
    unique_string = f"{concept}|{date_str}|{amount_str}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def load_user_data(user: str) -> pd.DataFrame:
    """
    Load consolidated transaction data for a user.
    
    Args:
        user: 'masha' or 'pablo'
        
    Returns:
        DataFrame with all user transactions
    """
    ensure_directories()
    
    filepath = get_user_data_file(user)
    
    if not filepath.exists():
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        
        # Parse dates
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        return df
    except Exception:
        return pd.DataFrame()


def save_user_data(user: str, df: pd.DataFrame) -> str:
    """
    Save consolidated transaction data for a user.
    
    Args:
        user: 'masha' or 'pablo'
        df: DataFrame with all transactions
        
    Returns:
        Path to saved file
    """
    ensure_directories()
    
    filepath = get_user_data_file(user)
    
    # Ensure consistent column order
    output_columns = ['TransactionID', 'Concepto', 'Amount', 'Category', 'Date']
    available_columns = [col for col in output_columns if col in df.columns]
    
    # Add any extra columns
    for col in df.columns:
        if col not in available_columns:
            available_columns.append(col)
    
    df[available_columns].to_csv(filepath, index=False, encoding='utf-8')
    
    return str(filepath)


def merge_transactions(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int, int]:
    """
    Merge new transactions with existing data, detecting duplicates.
    Also updates categories for existing transactions that have empty categories.
    
    Args:
        existing_df: DataFrame with existing transactions
        new_df: DataFrame with new transactions to add
        
    Returns:
        Tuple of (merged DataFrame, new_count, duplicate_count, updated_count)
    """
    # Add transaction IDs to new data
    new_df = new_df.copy()
    new_df['TransactionID'] = new_df.apply(create_transaction_id, axis=1)
    
    if existing_df.empty:
        # No existing data - all are new
        return new_df, len(new_df), 0, 0
    
    # Ensure existing data has transaction IDs
    if 'TransactionID' not in existing_df.columns:
        existing_df = existing_df.copy()
        existing_df['TransactionID'] = existing_df.apply(create_transaction_id, axis=1)
    else:
        existing_df = existing_df.copy()
    
    # Find existing transaction IDs
    existing_ids = set(existing_df['TransactionID'].values)
    
    # Split new data into truly new and potential updates
    is_new = ~new_df['TransactionID'].isin(existing_ids)
    truly_new = new_df[is_new]
    duplicates = new_df[~is_new]
    
    # For duplicates, check if we can update categories on existing uncategorized records
    updated_count = 0
    if not duplicates.empty:
        for _, dup_row in duplicates.iterrows():
            tid = dup_row['TransactionID']
            new_category = dup_row.get('Category', '')
            
            if new_category and new_category not in [None, '', 'nan']:
                # Find matching existing row
                mask = existing_df['TransactionID'] == tid
                if mask.any():
                    existing_cat = existing_df.loc[mask, 'Category'].iloc[0]
                    # Update if existing category is empty/None
                    if pd.isna(existing_cat) or existing_cat == '' or existing_cat == 'nan':
                        existing_df.loc[mask, 'Category'] = new_category
                        updated_count += 1
    
    duplicates_count = len(duplicates) - updated_count
    
    if truly_new.empty:
        # All duplicates (some may have been updated)
        return existing_df, 0, duplicates_count, updated_count
    
    # Merge new transactions with existing
    merged = pd.concat([existing_df, truly_new], ignore_index=True)
    
    # Sort by date (most recent first)
    if 'Date' in merged.columns:
        merged = merged.sort_values('Date', ascending=False, na_position='last')
    
    return merged, len(truly_new), duplicates_count, updated_count


def get_uncategorized_existing(user: str, new_df: pd.DataFrame) -> pd.DataFrame:
    """
    Get existing transactions that match new data but have empty categories.
    Used to show user which existing records need categorization.
    
    Args:
        user: User name
        new_df: New transactions being uploaded
        
    Returns:
        DataFrame of existing uncategorized transactions that match new data
    """
    existing_df = load_user_data(user)
    
    if existing_df.empty:
        return pd.DataFrame()
    
    # Generate IDs for comparison
    new_df = new_df.copy()
    new_df['TransactionID'] = new_df.apply(create_transaction_id, axis=1)
    
    if 'TransactionID' not in existing_df.columns:
        existing_df['TransactionID'] = existing_df.apply(create_transaction_id, axis=1)
    
    # Find matching records with empty categories
    matching_ids = set(new_df['TransactionID'].values)
    
    uncategorized_mask = (
        existing_df['TransactionID'].isin(matching_ids) & 
        (existing_df['Category'].isna() | (existing_df['Category'] == '') | (existing_df['Category'] == 'nan'))
    )
    
    return existing_df[uncategorized_mask].copy()


def add_transactions(user: str, new_df: pd.DataFrame) -> Tuple[str, int, int, int]:
    """
    Add new transactions for a user with smart merging.
    
    This is the main function to use when saving new data.
    It handles duplicate detection, merging, and category updates automatically.
    
    Args:
        user: 'masha' or 'pablo'
        new_df: DataFrame with new transactions
        
    Returns:
        Tuple of (filepath, new_count, duplicate_count, updated_count)
    """
    # Load existing data
    existing_df = load_user_data(user)
    
    # Merge with duplicate detection and category updates
    merged_df, new_count, dup_count, updated_count = merge_transactions(existing_df, new_df)
    
    # Save merged data
    filepath = save_user_data(user, merged_df)
    
    return filepath, new_count, dup_count, updated_count


def load_all_data() -> dict:
    """
    Load all data for both users.
    
    Returns:
        Dict with 'masha' and 'pablo' DataFrames
    """
    return {
        'masha': load_user_data('masha'),
        'pablo': load_user_data('pablo')
    }


def get_available_months(user: Optional[str] = None) -> list:
    """
    Get list of available months with data.
    
    Args:
        user: Optional filter by user, or None for all
        
    Returns:
        List of month-year strings sorted descending
    """
    if user:
        data = load_user_data(user)
    else:
        all_data = load_all_data()
        data = pd.concat([all_data['masha'], all_data['pablo']], ignore_index=True)
    
    if data.empty or 'Date' not in data.columns:
        return []
    
    valid_dates = data['Date'].dropna()
    if valid_dates.empty:
        return []
    
    months = valid_dates.dt.to_period('M').unique()
    return sorted([str(m) for m in months], reverse=True)


def get_available_years(user: Optional[str] = None) -> list:
    """
    Get list of available years with data.
    
    Args:
        user: Optional filter by user, or None for all
        
    Returns:
        List of year integers sorted descending
    """
    if user:
        data = load_user_data(user)
    else:
        all_data = load_all_data()
        data = pd.concat([all_data['masha'], all_data['pablo']], ignore_index=True)
    
    if data.empty or 'Date' not in data.columns:
        return []
    
    valid_dates = data['Date'].dropna()
    if valid_dates.empty:
        return []
    
    years = valid_dates.dt.year.unique()
    return sorted([int(y) for y in years], reverse=True)


def get_date_range(user: Optional[str] = None) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Get the date range of available data.
    
    Args:
        user: Optional filter by user, or None for all
        
    Returns:
        Tuple of (min_date, max_date) or (None, None) if no data
    """
    if user:
        data = load_user_data(user)
    else:
        all_data = load_all_data()
        data = pd.concat([all_data['masha'], all_data['pablo']], ignore_index=True)
    
    if data.empty or 'Date' not in data.columns:
        return None, None
    
    valid_dates = data['Date'].dropna()
    if valid_dates.empty:
        return None, None
    
    return valid_dates.min(), valid_dates.max()
