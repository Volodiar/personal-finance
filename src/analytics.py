"""
analytics.py - Charts and KPI calculations.

Provides visualization functions using Plotly for expense analysis
with daily, monthly, annual, and category-based views.
Shows income, expenses, and balance clearly separated.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Tuple
from datetime import datetime, timedelta
import calendar

from categories import get_category_color, ALL_CATEGORIES


# ============================================================================
# KPI CALCULATIONS
# ============================================================================

def calculate_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate comprehensive financial KPIs.
    
    Returns:
        Dict with income, expenses, balance, savings rate, and more
    """
    kpis = {
        'total_income': 0.0,
        'total_expenses': 0.0,
        'balance': 0.0,
        'savings_rate': 0.0,
        'expense_count': 0,
        'income_count': 0,
        'avg_expense': 0.0,
        'avg_income': 0.0,
        'top_category': 'N/A',
        'top_category_amount': 0.0,
        'top_category_percent': 0.0
    }
    
    if df.empty or 'Amount' not in df.columns:
        return kpis
    
    # Income: positive amounts
    income_df = df[df['Amount'] > 0]
    if not income_df.empty:
        kpis['total_income'] = income_df['Amount'].sum()
        kpis['income_count'] = len(income_df)
        kpis['avg_income'] = income_df['Amount'].mean()
    
    # Expenses: negative amounts (excluding Income category if present)
    expenses_mask = df['Amount'] < 0
    if 'Category' in df.columns:
        expenses_mask = expenses_mask & (df['Category'] != 'Income')
    expenses_df = df[expenses_mask]
    
    if not expenses_df.empty:
        kpis['total_expenses'] = expenses_df['Amount'].abs().sum()
        kpis['expense_count'] = len(expenses_df)
        kpis['avg_expense'] = expenses_df['Amount'].abs().mean()
        
        # Top category
        if 'Category' in expenses_df.columns:
            cat_totals = expenses_df.groupby('Category')['Amount'].sum().abs()
            if not cat_totals.empty:
                kpis['top_category'] = cat_totals.idxmax()
                kpis['top_category_amount'] = cat_totals.max()
                kpis['top_category_percent'] = (cat_totals.max() / kpis['total_expenses']) * 100
    
    # Balance and savings rate
    kpis['balance'] = kpis['total_income'] - kpis['total_expenses']
    if kpis['total_income'] > 0:
        kpis['savings_rate'] = (kpis['balance'] / kpis['total_income']) * 100
    
    return kpis


def get_category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get detailed category breakdown for expenses.
    
    Returns:
        DataFrame with Category, Amount, Percent, Transactions
    """
    if df.empty or 'Category' not in df.columns or 'Amount' not in df.columns:
        return pd.DataFrame()
    
    # Filter expenses only
    expenses = df[(df['Amount'] < 0) & (df['Category'] != 'Income')].copy()
    
    if expenses.empty:
        return pd.DataFrame()
    
    total_expenses = expenses['Amount'].abs().sum()
    
    breakdown = expenses.groupby('Category').agg({
        'Amount': ['sum', 'count']
    })
    breakdown.columns = ['Amount', 'Transactions']
    breakdown['Amount'] = breakdown['Amount'].abs()
    breakdown['Percent'] = (breakdown['Amount'] / total_expenses * 100).round(1)
    breakdown = breakdown.sort_values('Amount', ascending=False).reset_index()
    
    return breakdown


# ============================================================================
# OVERVIEW CHARTS
# ============================================================================

def create_category_pie_chart(df: pd.DataFrame, title: str = "Expenses by Category") -> go.Figure:
    """Create a pie chart showing expense distribution by category (expenses only)."""
    if df.empty or 'Category' not in df.columns:
        return _create_empty_chart("No data available")
    
    # Filter only expenses (negative amounts, excluding Income)
    expenses_df = df[(df['Amount'] < 0) & (df['Category'] != 'Income')]
    
    if expenses_df.empty:
        return _create_empty_chart("No expenses found")
    
    # Group by category
    category_totals = expenses_df.groupby('Category')['Amount'].sum().abs().reset_index()
    category_totals.columns = ['Category', 'Amount']
    category_totals = category_totals[category_totals['Amount'] > 0]
    
    if category_totals.empty:
        return _create_empty_chart("No expenses found")
    
    colors = [get_category_color(cat) for cat in category_totals['Category']]
    
    fig = px.pie(
        category_totals,
        values='Amount',
        names='Category',
        title=title,
        color_discrete_sequence=colors,
        hole=0.4
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>€%{value:,.2f}<br>%{percent}<extra></extra>'
    )
    
    fig.update_layout(
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    
    return fig


def create_income_expense_trend(df: pd.DataFrame, title: str = "Income vs Expenses") -> go.Figure:
    """
    Create a dual-line chart showing Income and Expenses trend over time.
    This replaces the buggy create_trend_chart.
    """
    if df.empty or 'Date' not in df.columns or 'Amount' not in df.columns:
        return _create_empty_chart("No trend data available")
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    if df.empty:
        return _create_empty_chart("No trend data available")
    
    df['Month'] = df['Date'].dt.to_period('M')
    
    # Calculate monthly income and expenses separately
    income = df[df['Amount'] > 0].groupby('Month')['Amount'].sum()
    expenses = df[df['Amount'] < 0].groupby('Month')['Amount'].sum().abs()
    
    # Get all months
    all_months = sorted(set(income.index) | set(expenses.index))
    
    if not all_months:
        return _create_empty_chart("No trend data available")
    
    month_labels = [str(m) for m in all_months]
    income_values = [income.get(m, 0) for m in all_months]
    expense_values = [expenses.get(m, 0) for m in all_months]
    balance_values = [income_values[i] - expense_values[i] for i in range(len(all_months))]
    
    fig = go.Figure()
    
    # Income line
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=income_values,
        name='Income',
        mode='lines+markers',
        line=dict(color='#2ECC71', width=3),
        marker=dict(size=8),
        hovertemplate='Income: €%{y:,.2f}<extra></extra>'
    ))
    
    # Expenses line
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=expense_values,
        name='Expenses',
        mode='lines+markers',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=8),
        hovertemplate='Expenses: €%{y:,.2f}<extra></extra>'
    ))
    
    # Balance line (dashed)
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=balance_values,
        name='Balance',
        mode='lines+markers',
        line=dict(color='#4ECDC4', width=2, dash='dash'),
        marker=dict(size=6),
        hovertemplate='Balance: €%{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Month',
        yaxis_title='Amount (€)',
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(tickangle=-45),
        hovermode='x unified'
    )
    
    return fig


def create_financial_summary_bar(df: pd.DataFrame) -> go.Figure:
    """Create a simple bar chart showing Income vs Expenses totals."""
    if df.empty or 'Amount' not in df.columns:
        return _create_empty_chart("No data available")
    
    income = df[df['Amount'] > 0]['Amount'].sum()
    expenses = df[df['Amount'] < 0]['Amount'].abs().sum()
    balance = income - expenses
    
    fig = go.Figure(data=[
        go.Bar(
            x=['Income', 'Expenses', 'Balance'],
            y=[income, expenses, balance],
            marker_color=['#2ECC71', '#FF6B6B', '#4ECDC4' if balance >= 0 else '#FF6B9D'],
            text=[f'€{income:,.0f}', f'€{expenses:,.0f}', f'€{balance:,.0f}'],
            textposition='outside',
            hovertemplate='%{x}: €%{y:,.2f}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='Financial Summary',
        yaxis_title='Amount (€)',
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig


# ============================================================================
# DAILY VIEW
# ============================================================================

def create_daily_chart_all(df: pd.DataFrame, start_date: datetime = None, end_date: datetime = None) -> go.Figure:
    """
    Create a bar chart showing daily spending for a date range.
    Shows all data by default if no dates specified.
    """
    if df.empty or 'Date' not in df.columns or 'Amount' not in df.columns:
        return _create_empty_chart("No data available")
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Apply date filter if specified
    if start_date:
        df = df[df['Date'] >= start_date]
    if end_date:
        df = df[df['Date'] <= end_date]
    
    if df.empty:
        return _create_empty_chart("No data in selected range")
    
    # Group by date
    daily_expenses = df[df['Amount'] < 0].groupby(df['Date'].dt.date)['Amount'].sum().abs()
    daily_income = df[df['Amount'] > 0].groupby(df['Date'].dt.date)['Amount'].sum()
    
    all_dates = sorted(set(daily_expenses.index) | set(daily_income.index))
    
    if not all_dates:
        return _create_empty_chart("No daily data available")
    
    date_labels = [d.strftime('%Y-%m-%d') for d in all_dates]
    expense_values = [daily_expenses.get(d, 0) for d in all_dates]
    income_values = [daily_income.get(d, 0) for d in all_dates]
    
    # Calculate cumulative balance
    cumulative = []
    running = 0
    for d in all_dates:
        running += daily_income.get(d, 0) - daily_expenses.get(d, 0)
        cumulative.append(running)
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Expense bars
    fig.add_trace(
        go.Bar(
            x=date_labels,
            y=expense_values,
            name='Expenses',
            marker_color='#FF6B6B',
            hovertemplate='%{x}<br>Expenses: €%{y:,.2f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Income bars (stacked on top concept, but we'll use grouped)
    fig.add_trace(
        go.Bar(
            x=date_labels,
            y=income_values,
            name='Income',
            marker_color='#2ECC71',
            hovertemplate='%{x}<br>Income: €%{y:,.2f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Cumulative balance line
    fig.add_trace(
        go.Scatter(
            x=date_labels,
            y=cumulative,
            name='Cumulative Balance',
            mode='lines',
            line=dict(color='#4ECDC4', width=2),
            hovertemplate='%{x}<br>Cumulative: €%{y:,.2f}<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title='Daily Transactions',
        barmode='group',
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(tickangle=-45)
    )
    
    fig.update_yaxes(title_text="Daily Amount (€)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative Balance (€)", secondary_y=True)
    
    return fig


def get_daily_summary(df: pd.DataFrame, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Get daily summary with income, expenses, and cumulative balance."""
    if df.empty or 'Date' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    if start_date:
        df = df[df['Date'] >= start_date]
    if end_date:
        df = df[df['Date'] <= end_date]
    
    if df.empty:
        return pd.DataFrame()
    
    # Group by date
    income = df[df['Amount'] > 0].groupby(df['Date'].dt.date)['Amount'].sum()
    expenses = df[df['Amount'] < 0].groupby(df['Date'].dt.date)['Amount'].sum().abs()
    count = df.groupby(df['Date'].dt.date)['Amount'].count()
    
    all_dates = sorted(set(income.index) | set(expenses.index))
    
    summary = pd.DataFrame({
        'Date': all_dates,
        'Income': [income.get(d, 0) for d in all_dates],
        'Expenses': [expenses.get(d, 0) for d in all_dates],
        'Transactions': [count.get(d, 0) for d in all_dates]
    })
    
    summary['Net'] = summary['Income'] - summary['Expenses']
    summary['Cumulative'] = summary['Net'].cumsum()
    
    return summary.round(2)


# ============================================================================
# MONTHLY VIEW
# ============================================================================

def create_monthly_chart(df: pd.DataFrame, year: Optional[int] = None) -> go.Figure:
    """Create a grouped bar chart showing monthly income and expenses."""
    if df.empty or 'Date' not in df.columns or 'Amount' not in df.columns:
        return _create_empty_chart("No data available")
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    if year:
        df = df[df['Date'].dt.year == year]
    
    if df.empty:
        return _create_empty_chart(f"No data for {year}" if year else "No data available")
    
    df['YearMonth'] = df['Date'].dt.to_period('M')
    
    income = df[df['Amount'] > 0].groupby('YearMonth')['Amount'].sum()
    expenses = df[df['Amount'] < 0].groupby('YearMonth')['Amount'].sum().abs()
    
    all_months = sorted(set(income.index) | set(expenses.index))
    month_labels = [str(m) for m in all_months]
    income_values = [income.get(m, 0) for m in all_months]
    expense_values = [expenses.get(m, 0) for m in all_months]
    balance_values = [income_values[i] - expense_values[i] for i in range(len(all_months))]
    cumulative = []
    running = 0
    for b in balance_values:
        running += b
        cumulative.append(running)
    
    title = f'Monthly Overview - {year}' if year else 'Monthly Overview (All Time)'
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(x=month_labels, y=income_values, name='Income', 
               marker_color='#2ECC71',
               hovertemplate='%{x}<br>Income: €%{y:,.2f}<extra></extra>'),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Bar(x=month_labels, y=expense_values, name='Expenses',
               marker_color='#FF6B6B',
               hovertemplate='%{x}<br>Expenses: €%{y:,.2f}<extra></extra>'),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(x=month_labels, y=cumulative, name='Cumulative Balance',
                   mode='lines+markers', line=dict(color='#4ECDC4', width=3),
                   hovertemplate='%{x}<br>Cumulative: €%{y:,.2f}<extra></extra>'),
        secondary_y=True
    )
    
    fig.update_layout(
        title=title,
        barmode='group',
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(tickangle=-45)
    )
    
    fig.update_yaxes(title_text="Monthly Amount (€)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative Balance (€)", secondary_y=True)
    
    return fig


def get_monthly_summary(df: pd.DataFrame, year: Optional[int] = None) -> pd.DataFrame:
    """Get monthly summary with income, expenses, balance, and cumulative."""
    if df.empty or 'Date' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    if year:
        df = df[df['Date'].dt.year == year]
    
    if df.empty:
        return pd.DataFrame()
    
    df['Month'] = df['Date'].dt.to_period('M')
    
    income = df[df['Amount'] > 0].groupby('Month')['Amount'].sum()
    expenses = df[df['Amount'] < 0].groupby('Month')['Amount'].sum().abs()
    count = df.groupby('Month')['Amount'].count()
    
    all_months = sorted(set(income.index) | set(expenses.index))
    
    summary = pd.DataFrame({
        'Month': [str(m) for m in all_months],
        'Income': [income.get(m, 0) for m in all_months],
        'Expenses': [expenses.get(m, 0) for m in all_months],
        'Transactions': [count.get(m, 0) for m in all_months]
    })
    
    summary['Balance'] = summary['Income'] - summary['Expenses']
    summary['Cumulative'] = summary['Balance'].cumsum()
    summary['Savings %'] = ((summary['Balance'] / summary['Income']) * 100).fillna(0).round(1)
    
    return summary.round(2)


# ============================================================================
# ANNUAL VIEW
# ============================================================================

def create_annual_chart(df: pd.DataFrame) -> go.Figure:
    """Create a bar chart comparing income, expenses, and balance by year."""
    if df.empty or 'Date' not in df.columns or 'Amount' not in df.columns:
        return _create_empty_chart("No data available")
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Year'] = df['Date'].dt.year
    
    income = df[df['Amount'] > 0].groupby('Year')['Amount'].sum()
    expenses = df[df['Amount'] < 0].groupby('Year')['Amount'].sum().abs()
    
    all_years = sorted(set(income.index) | set(expenses.index))
    
    if not all_years:
        return _create_empty_chart("No annual data available")
    
    year_labels = [str(y) for y in all_years]
    income_values = [income.get(y, 0) for y in all_years]
    expense_values = [expenses.get(y, 0) for y in all_years]
    balance_values = [income_values[i] - expense_values[i] for i in range(len(all_years))]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=year_labels, y=income_values, name='Income',
        marker_color='#2ECC71',
        hovertemplate='%{x}<br>Income: €%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=year_labels, y=expense_values, name='Expenses',
        marker_color='#FF6B6B',
        hovertemplate='%{x}<br>Expenses: €%{y:,.2f}<extra></extra>'
    ))
    
    # Balance as line
    fig.add_trace(go.Scatter(
        x=year_labels, y=balance_values, name='Net Balance',
        mode='lines+markers',
        line=dict(color='#4ECDC4', width=3),
        marker=dict(size=10),
        hovertemplate='%{x}<br>Balance: €%{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Annual Overview',
        barmode='group',
        xaxis_title='Year',
        yaxis_title='Amount (€)',
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return fig


def get_annual_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Get annual summary."""
    if df.empty or 'Date' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Year'] = df['Date'].dt.year
    
    income = df[df['Amount'] > 0].groupby('Year')['Amount'].sum()
    expenses = df[df['Amount'] < 0].groupby('Year')['Amount'].sum().abs()
    count = df.groupby('Year')['Amount'].count()
    
    all_years = sorted(set(income.index) | set(expenses.index))
    
    summary = pd.DataFrame({
        'Year': all_years,
        'Income': [income.get(y, 0) for y in all_years],
        'Expenses': [expenses.get(y, 0) for y in all_years],
        'Transactions': [count.get(y, 0) for y in all_years]
    })
    
    summary['Balance'] = summary['Income'] - summary['Expenses']
    summary['Savings %'] = ((summary['Balance'] / summary['Income']) * 100).fillna(0).round(1)
    
    return summary.round(2)


# ============================================================================
# CATEGORY VIEW
# ============================================================================

def create_category_breakdown_chart(df: pd.DataFrame, period: str = 'month') -> go.Figure:
    """Create a stacked bar chart showing category distribution over time."""
    if df.empty or 'Date' not in df.columns or 'Category' not in df.columns:
        return _create_empty_chart("No data available")
    
    # Filter only expenses
    df = df[(df['Amount'] < 0) & (df['Category'] != 'Income')].copy()
    
    if df.empty:
        return _create_empty_chart("No expense data available")
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = df['Amount'].abs()
    
    if period == 'day':
        df['Period'] = df['Date'].dt.date.astype(str)
    elif period == 'year':
        df['Period'] = df['Date'].dt.year.astype(str)
    else:
        df['Period'] = df['Date'].dt.to_period('M').astype(str)
    
    pivot = df.pivot_table(
        values='Amount', index='Period', columns='Category',
        aggfunc='sum', fill_value=0
    )
    
    if pivot.empty:
        return _create_empty_chart("No category data available")
    
    fig = go.Figure()
    
    for category in pivot.columns:
        color = get_category_color(category)
        fig.add_trace(go.Bar(
            name=category,
            x=pivot.index.tolist(),
            y=pivot[category].values,
            marker_color=color,
            hovertemplate=f'<b>{category}</b><br>%{{x}}<br>€%{{y:,.2f}}<extra></extra>'
        ))
    
    period_title = {'day': 'Daily', 'month': 'Monthly', 'year': 'Annual'}
    
    fig.update_layout(
        title=f'{period_title.get(period, "Monthly")} Category Breakdown',
        barmode='stack',
        xaxis_title='Period',
        yaxis_title='Amount (€)',
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        xaxis=dict(tickangle=-45)
    )
    
    return fig


def create_category_trend(df: pd.DataFrame, category: str) -> go.Figure:
    """Create a line chart showing trend for a specific category."""
    if df.empty or 'Date' not in df.columns or 'Category' not in df.columns:
        return _create_empty_chart("No data available")
    
    df = df[df['Category'] == category].copy()
    
    if df.empty:
        return _create_empty_chart(f"No data for {category}")
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Month'] = df['Date'].dt.to_period('M')
    
    monthly = df.groupby('Month')['Amount'].sum().abs().reset_index()
    monthly['Month'] = monthly['Month'].astype(str)
    
    color = get_category_color(category)
    
    fig = px.line(monthly, x='Month', y='Amount', title=f'{category} Trend', markers=True)
    
    fig.update_traces(
        line_color=color,
        marker_size=10,
        hovertemplate='%{x}<br>€%{y:,.2f}<extra></extra>'
    )
    
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Amount (€)',
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickangle=-45)
    )
    
    return fig


def get_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Get category summary for expenses."""
    return get_category_breakdown(df)


# ============================================================================
# COMPARISON
# ============================================================================

def create_comparison_bar_chart(masha_df: pd.DataFrame, pablo_df: pd.DataFrame) -> go.Figure:
    """Create side-by-side bar chart comparing expenses between users."""
    masha_totals = _get_category_totals(masha_df)
    pablo_totals = _get_category_totals(pablo_df)
    
    all_categories = set(masha_totals.keys()) | set(pablo_totals.keys())
    all_categories = {c for c in all_categories if c != 'Income'}
    
    if not all_categories:
        return _create_empty_chart("No data available for comparison")
    
    categories = sorted(list(all_categories))
    masha_values = [masha_totals.get(cat, 0) for cat in categories]
    pablo_values = [pablo_totals.get(cat, 0) for cat in categories]
    
    fig = go.Figure(data=[
        go.Bar(name='Masha', x=categories, y=masha_values, marker_color='#FF6B9D',
               hovertemplate='<b>Masha</b><br>%{x}: €%{y:,.2f}<extra></extra>'),
        go.Bar(name='Pablo', x=categories, y=pablo_values, marker_color='#4ECDC4',
               hovertemplate='<b>Pablo</b><br>%{x}: €%{y:,.2f}<extra></extra>')
    ])
    
    fig.update_layout(
        title='Expense Comparison by Category',
        barmode='group',
        xaxis_title='Category',
        yaxis_title='Amount (€)',
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickangle=-45)
    )
    
    return fig


# ============================================================================
# LEGACY FUNCTION (kept for compatibility but fixed)
# ============================================================================

def create_trend_chart(df: pd.DataFrame, title: str = "Spending Trend") -> go.Figure:
    """Create a line chart showing EXPENSES ONLY trend over time."""
    if df.empty or 'Date' not in df.columns or 'Amount' not in df.columns:
        return _create_empty_chart("No trend data available")
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # FIXED: Filter to expenses only (negative amounts)
    expenses = df[df['Amount'] < 0].copy()
    
    if expenses.empty:
        return _create_empty_chart("No expense data available")
    
    expenses['Month'] = expenses['Date'].dt.to_period('M')
    monthly = expenses.groupby('Month')['Amount'].sum().abs().reset_index()
    monthly['Month'] = monthly['Month'].astype(str)
    
    if monthly.empty:
        return _create_empty_chart("No trend data available")
    
    fig = px.line(monthly, x='Month', y='Amount', title=title, markers=True)
    
    fig.update_traces(
        line_color='#FF6B6B',  # Red for expenses
        marker_size=10,
        hovertemplate='<b>%{x}</b><br>€%{y:,.2f}<extra></extra>'
    )
    
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Total Expenses (€)',
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


# ============================================================================
# HELPERS
# ============================================================================

def _get_category_totals(df: pd.DataFrame) -> dict:
    """Get category totals for expenses."""
    if df.empty or 'Category' not in df.columns or 'Amount' not in df.columns:
        return {}
    
    expenses = df[(df['Amount'] < 0) & (df['Category'] != 'Income')]
    return expenses.groupby('Category')['Amount'].sum().abs().to_dict()


def _create_empty_chart(message: str) -> go.Figure:
    """Create an empty chart with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="gray")
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
    )
    return fig
