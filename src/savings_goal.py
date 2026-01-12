"""
savings_goal.py - Monthly savings goal tracking.

Stores and tracks monthly savings goals with progress analysis.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import pandas as pd


# Savings goal storage path
CONFIG_DIR = Path("config")
SAVINGS_FILE = CONFIG_DIR / "savings_goal.json"


def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_savings_goal() -> Dict:
    """Load savings goal configuration."""
    ensure_config_dir()
    
    if SAVINGS_FILE.exists():
        with open(SAVINGS_FILE, 'r') as f:
            return json.load(f)
    
    return {
        "monthly_target": 0.0,
        "enabled": False,
        "updated": None
    }


def save_savings_goal(target: float, enabled: bool = True):
    """Save monthly savings goal."""
    ensure_config_dir()
    
    data = {
        "monthly_target": target,
        "enabled": enabled,
        "updated": datetime.now().isoformat()
    }
    
    with open(SAVINGS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_monthly_target() -> float:
    """Get monthly savings target amount."""
    goal = load_savings_goal()
    return goal.get("monthly_target", 0.0)


def is_goal_enabled() -> bool:
    """Check if savings goal tracking is enabled."""
    goal = load_savings_goal()
    return goal.get("enabled", False)


def calculate_savings_progress(df: pd.DataFrame) -> Dict:
    """
    Calculate progress towards monthly savings goal.
    
    Args:
        df: Transaction DataFrame
        
    Returns:
        Dict with progress metrics
    """
    goal = load_savings_goal()
    target = goal.get("monthly_target", 0.0)
    
    if not target or df.empty:
        return {
            "target": target,
            "actual_savings": 0.0,
            "progress_percent": 0.0,
            "difference": 0.0,
            "on_track": False,
            "monthly_income": 0.0,
            "monthly_expenses": 0.0
        }
    
    # Get current month data
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    now = datetime.now()
    
    current_month = df[
        (df['Date'].dt.month == now.month) &
        (df['Date'].dt.year == now.year)
    ]
    
    # Calculate income and expenses
    monthly_income = current_month[current_month['Amount'] > 0]['Amount'].sum()
    monthly_expenses = current_month[current_month['Amount'] < 0]['Amount'].abs().sum()
    actual_savings = monthly_income - monthly_expenses
    
    # Calculate progress
    progress_percent = (actual_savings / target * 100) if target > 0 else 0
    difference = actual_savings - target
    on_track = actual_savings >= target
    
    return {
        "target": target,
        "actual_savings": actual_savings,
        "progress_percent": min(progress_percent, 150),  # Cap at 150%
        "difference": difference,
        "on_track": on_track,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses
    }


def get_category_variance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze which categories exceeded their typical spending.
    
    Returns:
        DataFrame with category, current_month, average, difference
    """
    if df.empty or 'Category' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    now = datetime.now()
    
    # Current month expenses
    current = df[
        (df['Date'].dt.month == now.month) &
        (df['Date'].dt.year == now.year) &
        (df['Amount'] < 0)
    ]
    current_by_cat = current.groupby('Category')['Amount'].sum().abs()
    
    # Historical average
    historical = df[
        ~((df['Date'].dt.month == now.month) & (df['Date'].dt.year == now.year)) &
        (df['Amount'] < 0)
    ]
    
    if historical.empty:
        return pd.DataFrame()
    
    historical['YearMonth'] = historical['Date'].dt.to_period('M')
    num_months = max(1, historical['YearMonth'].nunique())
    
    historical_by_cat = historical.groupby('Category')['Amount'].sum().abs() / num_months
    
    # Build variance table
    variance = []
    for cat in current_by_cat.index:
        current_amt = current_by_cat.get(cat, 0)
        avg_amt = historical_by_cat.get(cat, 0)
        diff = current_amt - avg_amt
        
        if diff > 0:
            variance.append({
                "Category": cat,
                "This Month": current_amt,
                "Average": avg_amt,
                "Over Budget": diff
            })
    
    result = pd.DataFrame(variance)
    if not result.empty:
        result = result.sort_values("Over Budget", ascending=False)
    
    return result
