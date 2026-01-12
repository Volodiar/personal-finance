"""
insights.py - Recurring Transactions Detection and Predictive Insights.

Provides detection of recurring payments (subscriptions, fixed costs),
spending projections, and anomaly detection for smart alerts.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict
import re


def detect_recurring_transactions(df: pd.DataFrame, tolerance_days: int = 5) -> List[Dict]:
    """
    Detect recurring transactions based on concept and amount patterns.
    
    Args:
        df: DataFrame with transactions
        tolerance_days: Days of tolerance for interval matching
        
    Returns:
        List of detected recurring transactions
    """
    if df.empty or 'Date' not in df.columns or 'Concepto' not in df.columns:
        return []
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Group by concept
    concept_groups = df.groupby('Concepto')
    
    recurring = []
    
    for concept, group in concept_groups:
        if len(group) < 2:
            continue
        
        # Sort by date
        group = group.sort_values('Date')
        dates = group['Date'].tolist()
        amounts = group['Amount'].tolist()
        
        # Check if amounts are similar (within 5% tolerance)
        avg_amount = sum(amounts) / len(amounts)
        amount_consistent = all(abs(a - avg_amount) / abs(avg_amount) < 0.05 for a in amounts if avg_amount != 0)
        
        if not amount_consistent and len(set(amounts)) > 2:
            continue
        
        # Calculate intervals between transactions
        intervals = []
        for i in range(1, len(dates)):
            delta = (dates[i] - dates[i-1]).days
            intervals.append(delta)
        
        if not intervals:
            continue
        
        avg_interval = sum(intervals) / len(intervals)
        
        # Determine frequency
        frequency = None
        expected_interval = None
        
        if 25 <= avg_interval <= 35:
            frequency = "monthly"
            expected_interval = 30
        elif 6 <= avg_interval <= 8:
            frequency = "weekly"
            expected_interval = 7
        elif 12 <= avg_interval <= 16:
            frequency = "bi-weekly"
            expected_interval = 14
        elif 85 <= avg_interval <= 95:
            frequency = "quarterly"
            expected_interval = 90
        elif 355 <= avg_interval <= 375:
            frequency = "yearly"
            expected_interval = 365
        
        if frequency:
            # Check consistency
            consistent = all(abs(i - expected_interval) <= tolerance_days for i in intervals)
            
            if consistent or len(intervals) >= 3:
                last_date = max(dates)
                next_expected = last_date + timedelta(days=expected_interval)
                
                recurring.append({
                    'concept': concept,
                    'amount': round(avg_amount, 2),
                    'frequency': frequency,
                    'occurrences': len(group),
                    'last_date': last_date.strftime('%Y-%m-%d'),
                    'next_expected': next_expected.strftime('%Y-%m-%d'),
                    'category': group['Category'].mode().iloc[0] if 'Category' in group.columns and not group['Category'].mode().empty else 'Unknown',
                    'is_expense': avg_amount < 0
                })
    
    # Sort by amount (biggest first)
    recurring.sort(key=lambda x: abs(x['amount']), reverse=True)
    
    return recurring


def get_monthly_fixed_costs(recurring: List[Dict]) -> float:
    """Calculate total monthly fixed costs from recurring transactions."""
    total = 0.0
    
    for item in recurring:
        if not item['is_expense']:
            continue
            
        amount = abs(item['amount'])
        freq = item['frequency']
        
        if freq == 'monthly':
            total += amount
        elif freq == 'weekly':
            total += amount * 4.33
        elif freq == 'bi-weekly':
            total += amount * 2.17
        elif freq == 'quarterly':
            total += amount / 3
        elif freq == 'yearly':
            total += amount / 12
    
    return round(total, 2)


def calculate_spending_velocity(df: pd.DataFrame) -> Dict:
    """
    Calculate daily spending rate and projections.
    
    Returns:
        Dict with daily_rate, projected_month, days_in_month, etc.
    """
    if df.empty or 'Date' not in df.columns or 'Amount' not in df.columns:
        return {'daily_rate': 0, 'projected_month': 0}
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    now = datetime.now()
    
    # Get current month's data
    current_month = df[
        (df['Date'].dt.month == now.month) &
        (df['Date'].dt.year == now.year)
    ]
    
    # Expenses only
    expenses = current_month[current_month['Amount'] < 0]
    
    if expenses.empty:
        return {
            'daily_rate': 0,
            'projected_month': 0,
            'current_spent': 0,
            'days_passed': now.day,
            'days_remaining': (pd.Timestamp(now.year, now.month, 1) + pd.offsets.MonthEnd(0)).day - now.day
        }
    
    total_spent = expenses['Amount'].abs().sum()
    days_passed = now.day
    daily_rate = total_spent / days_passed if days_passed > 0 else 0
    
    # Days in current month
    days_in_month = (pd.Timestamp(now.year, now.month, 1) + pd.offsets.MonthEnd(0)).day
    projected_month = daily_rate * days_in_month
    days_remaining = days_in_month - days_passed
    
    return {
        'daily_rate': round(daily_rate, 2),
        'projected_month': round(projected_month, 2),
        'current_spent': round(total_spent, 2),
        'days_passed': days_passed,
        'days_remaining': days_remaining,
        'days_in_month': days_in_month
    }


def detect_anomalies(df: pd.DataFrame, threshold: float = 0.3) -> List[Dict]:
    """
    Detect spending anomalies - categories where current month is significantly
    higher than average.
    
    Args:
        df: Transaction DataFrame
        threshold: Percent above average to flag (0.3 = 30%)
        
    Returns:
        List of anomaly alerts
    """
    if df.empty or 'Date' not in df.columns or 'Category' not in df.columns:
        return []
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Expenses only
    expenses = df[df['Amount'] < 0].copy()
    
    if expenses.empty:
        return []
    
    now = datetime.now()
    
    # Current month spending by category
    current = expenses[
        (expenses['Date'].dt.month == now.month) &
        (expenses['Date'].dt.year == now.year)
    ]
    current_by_cat = current.groupby('Category')['Amount'].sum().abs()
    
    # Historical average (exclude current month)
    historical = expenses[
        ~((expenses['Date'].dt.month == now.month) & 
          (expenses['Date'].dt.year == now.year))
    ]
    
    if historical.empty:
        return []
    
    # Get number of months in history
    historical['YearMonth'] = historical['Date'].dt.to_period('M')
    num_months = historical['YearMonth'].nunique()
    
    if num_months == 0:
        return []
    
    historical_total = historical.groupby('Category')['Amount'].sum().abs()
    historical_avg = historical_total / num_months
    
    # Find anomalies
    anomalies = []
    
    for cat in current_by_cat.index:
        current_amount = current_by_cat.get(cat, 0)
        avg_amount = historical_avg.get(cat, 0)
        
        if avg_amount == 0:
            continue
        
        percent_diff = (current_amount - avg_amount) / avg_amount
        
        if percent_diff > threshold:
            anomalies.append({
                'category': cat,
                'current_amount': round(current_amount, 2),
                'average_amount': round(avg_amount, 2),
                'percent_above': round(percent_diff * 100, 0),
                'extra_spent': round(current_amount - avg_amount, 2)
            })
    
    # Sort by percent above average
    anomalies.sort(key=lambda x: x['percent_above'], reverse=True)
    
    return anomalies


def get_prediction_insights(df: pd.DataFrame) -> List[Dict]:
    """
    Generate prediction-based insights for display.
    
    Returns:
        List of insight cards to display
    """
    insights = []
    
    # Spending velocity
    velocity = calculate_spending_velocity(df)
    if velocity['daily_rate'] > 0:
        insights.append({
            'type': 'velocity',
            'icon': '📈',
            'title': 'Spending Rate',
            'message': f"You're spending €{velocity['daily_rate']:.0f}/day. At this rate, you'll spend €{velocity['projected_month']:.0f} this month.",
            'level': 'info'
        })
    
    # Anomalies
    anomalies = detect_anomalies(df)
    for anomaly in anomalies[:3]:  # Top 3
        level = 'warning' if anomaly['percent_above'] < 50 else 'danger'
        insights.append({
            'type': 'anomaly',
            'icon': '⚠️',
            'title': f"{anomaly['category']} Spike",
            'message': f"{anomaly['percent_above']:.0f}% above average (€{anomaly['extra_spent']:.0f} extra)",
            'level': level
        })
    
    return insights


def get_transaction_calendar(df: pd.DataFrame, year: int, month: int) -> Dict:
    """
    Get transactions organized by day for calendar display.
    
    Returns:
        Dict with day -> [transactions]
    """
    if df.empty or 'Date' not in df.columns:
        return {}
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    month_data = df[
        (df['Date'].dt.month == month) &
        (df['Date'].dt.year == year)
    ]
    
    calendar = defaultdict(list)
    
    for _, row in month_data.iterrows():
        day = row['Date'].day
        calendar[day].append({
            'concept': row.get('Concepto', ''),
            'amount': row.get('Amount', 0),
            'category': row.get('Category', 'Unknown')
        })
    
    return dict(calendar)
