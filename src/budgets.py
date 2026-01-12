"""
budgets.py - Budget and Goals management.

Handles budget limits per category, goal tracking, and calculations
for budget consumption and progress.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd


# Budget storage path
BUDGET_FILE = Path("config/budgets.json")


def ensure_budget_file():
    """Ensure budget file exists with default structure."""
    if not BUDGET_FILE.exists():
        default_budgets = {
            "masha": {
                "monthly_budgets": {},
                "goals": []
            },
            "pablo": {
                "monthly_budgets": {},
                "goals": []
            }
        }
        BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BUDGET_FILE, 'w') as f:
            json.dump(default_budgets, f, indent=2)


def load_budgets() -> dict:
    """Load all budget data."""
    ensure_budget_file()
    with open(BUDGET_FILE, 'r') as f:
        return json.load(f)


def save_budgets(data: dict):
    """Save budget data."""
    ensure_budget_file()
    with open(BUDGET_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_user_budgets(user: str) -> dict:
    """Get monthly budgets for a user."""
    data = load_budgets()
    return data.get(user, {}).get("monthly_budgets", {})


def set_category_budget(user: str, category: str, amount: float):
    """Set a monthly budget for a category."""
    data = load_budgets()
    if user not in data:
        data[user] = {"monthly_budgets": {}, "goals": []}
    data[user]["monthly_budgets"][category] = amount
    save_budgets(data)


def remove_category_budget(user: str, category: str):
    """Remove a category budget."""
    data = load_budgets()
    if user in data and category in data[user]["monthly_budgets"]:
        del data[user]["monthly_budgets"][category]
        save_budgets(data)


def get_user_goals(user: str) -> list:
    """Get goals for a user."""
    data = load_budgets()
    return data.get(user, {}).get("goals", [])


def add_goal(user: str, name: str, target_amount: float, 
             deadline: Optional[str] = None, description: str = ""):
    """Add a savings goal."""
    data = load_budgets()
    if user not in data:
        data[user] = {"monthly_budgets": {}, "goals": []}
    
    goal = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "name": name,
        "target_amount": target_amount,
        "current_amount": 0.0,
        "deadline": deadline,
        "description": description,
        "created": datetime.now().isoformat(),
        "completed": False
    }
    
    data[user]["goals"].append(goal)
    save_budgets(data)
    return goal["id"]


def update_goal_progress(user: str, goal_id: str, amount: float):
    """Update the current amount for a goal."""
    data = load_budgets()
    if user in data:
        for goal in data[user]["goals"]:
            if goal["id"] == goal_id:
                goal["current_amount"] = amount
                if amount >= goal["target_amount"]:
                    goal["completed"] = True
                break
        save_budgets(data)


def delete_goal(user: str, goal_id: str):
    """Delete a goal."""
    data = load_budgets()
    if user in data:
        data[user]["goals"] = [
            g for g in data[user]["goals"] if g["id"] != goal_id
        ]
        save_budgets(data)


def calculate_budget_status(user: str, transactions: pd.DataFrame) -> dict:
    """
    Calculate budget consumption for all categories in current month.
    
    Returns:
        Dict with category -> {budget, spent, remaining, percent, status}
    """
    budgets = get_user_budgets(user)
    
    if not budgets:
        return {}
    
    # Get current month's transactions
    now = datetime.now()
    transactions = transactions.copy()
    transactions['Date'] = pd.to_datetime(transactions['Date'], errors='coerce')
    
    current_month = transactions[
        (transactions['Date'].dt.month == now.month) &
        (transactions['Date'].dt.year == now.year)
    ]
    
    # Calculate spending by category (only expenses)
    expenses = current_month[current_month['Amount'] < 0]
    if 'Category' not in expenses.columns:
        return {}
    
    category_spending = expenses.groupby('Category')['Amount'].sum().abs().to_dict()
    
    # Build status for each budgeted category
    status = {}
    for category, budget in budgets.items():
        spent = category_spending.get(category, 0)
        remaining = budget - spent
        percent = (spent / budget * 100) if budget > 0 else 0
        
        # Determine status
        if percent >= 100:
            level = "exceeded"
        elif percent >= 80:
            level = "warning"
        elif percent >= 50:
            level = "caution"
        else:
            level = "good"
        
        status[category] = {
            "budget": budget,
            "spent": spent,
            "remaining": remaining,
            "percent": percent,
            "status": level
        }
    
    return status


def calculate_goal_progress(user: str, transactions: pd.DataFrame) -> list:
    """
    Calculate progress on goals based on savings (income - expenses).
    
    Returns:
        List of goals with calculated progress
    """
    goals = get_user_goals(user)
    
    if not goals:
        return []
    
    # Calculate total balance as "savings"
    transactions = transactions.copy()
    total_income = transactions[transactions['Amount'] > 0]['Amount'].sum()
    total_expenses = transactions[transactions['Amount'] < 0]['Amount'].abs().sum()
    total_savings = total_income - total_expenses
    
    # Enrich goals with progress info
    enriched_goals = []
    for goal in goals:
        progress = {
            **goal,
            "progress_percent": min(100, (goal["current_amount"] / goal["target_amount"] * 100)) if goal["target_amount"] > 0 else 0,
            "amount_remaining": goal["target_amount"] - goal["current_amount"]
        }
        
        # Calculate days remaining if deadline exists
        if goal.get("deadline"):
            try:
                deadline = datetime.fromisoformat(goal["deadline"])
                days_remaining = (deadline - datetime.now()).days
                progress["days_remaining"] = max(0, days_remaining)
            except:
                progress["days_remaining"] = None
        else:
            progress["days_remaining"] = None
        
        enriched_goals.append(progress)
    
    return enriched_goals


def get_budget_alerts(user: str, transactions: pd.DataFrame) -> list:
    """
    Get list of budget alerts (warnings and exceeded).
    
    Returns:
        List of alert dicts with category, message, level
    """
    status = calculate_budget_status(user, transactions)
    alerts = []
    
    for category, info in status.items():
        if info["status"] == "exceeded":
            alerts.append({
                "category": category,
                "message": f"Budget exceeded! Spent €{info['spent']:.0f} of €{info['budget']:.0f}",
                "level": "danger",
                "percent": info["percent"]
            })
        elif info["status"] == "warning":
            alerts.append({
                "category": category,
                "message": f"Almost at limit: {info['percent']:.0f}% used (€{info['remaining']:.0f} left)",
                "level": "warning",
                "percent": info["percent"]
            })
    
    return sorted(alerts, key=lambda x: x["percent"], reverse=True)
