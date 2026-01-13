"""
data_processor.py - CSV parsing and data preprocessing.

Handles bank statement file parsing with dynamic header detection,
amount conversion, and date parsing for Spanish/Imagin Bank formats.
"""

import pandas as pd
import re
from datetime import datetime
from typing import Union, Optional, Tuple
from io import BytesIO, StringIO
import pdfplumber

from categories import categorize_concept


def preprocess_amount(importe_str: str) -> float:
    """
    Convert Spanish-format amount string to float.
    
    Handles Imagin Bank format with EUR suffix and Spanish thousand/decimal separators.
    
    Examples:
        "-36,00EUR" -> -36.00
        "3.980,53EUR" -> 3980.53
        "-1.234,56 EUR" -> -1234.56
        "1234.56" -> 1234.56 (already in decimal format)
        
    Args:
        importe_str: Amount string in Spanish format
        
    Returns:
        Float value of the amount
    """
    if pd.isna(importe_str) or importe_str == "":
        return 0.0
    
    # Convert to string if not already
    amount_str = str(importe_str).strip()
    
    if not amount_str:
        return 0.0
    
    # Remove currency symbols (EUR, €) and whitespace
    amount_str = re.sub(r'[€\s]', '', amount_str)
    amount_str = re.sub(r'EUR$', '', amount_str, flags=re.IGNORECASE)
    amount_str = amount_str.strip()
    
    if not amount_str:
        return 0.0
    
    # Handle Spanish number format: 3.980,53 -> 3980.53
    # Check if it's Spanish format (has comma as decimal separator)
    if ',' in amount_str:
        # Spanish format: dots are thousand separators, comma is decimal
        amount_str = amount_str.replace('.', '')  # Remove thousand separators
        amount_str = amount_str.replace(',', '.')  # Convert decimal separator
    # else: assume it's already in standard decimal format
    
    try:
        return float(amount_str)
    except ValueError:
        return 0.0


def parse_date(fecha_str: str) -> Optional[datetime]:
    """
    Parse Spanish date formats to datetime.
    
    Primary format: DD/MM/YYYY (Imagin Bank standard)
    
    Handles formats like:
        - "15/01/2024" (primary)
        - "15-01-2024"
        - "2024-01-15"
        
    Args:
        fecha_str: Date string
        
    Returns:
        Datetime object or None if unparseable
    """
    if pd.isna(fecha_str):
        return None
    
    fecha_str = str(fecha_str).strip()
    
    if not fecha_str:
        return None
    
    # Try common date formats (DD/MM/YYYY first as it's Imagin Bank standard)
    formats = [
        "%d/%m/%Y",     # 15/01/2024 (primary for Imagin Bank)
        "%d-%m-%Y",     # 15-01-2024
        "%Y-%m-%d",     # 2024-01-15
        "%d/%m/%y",     # 15/01/24
        "%d-%m-%y",     # 15-01-24
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(fecha_str, fmt)
        except ValueError:
            continue
    
    return None


def find_header_row(content: str, delimiter: str = ';') -> Tuple[int, list]:
    """
    Dynamically find the row containing the data headers.
    
    Scans the content to find a row containing the required headers:
    'Concepto', 'Fecha', and 'Importe' (case-insensitive).
    
    Args:
        content: File content as string
        delimiter: Column delimiter (default semicolon)
        
    Returns:
        Tuple of (row_index, list of column names) or (-1, []) if not found
    """
    lines = content.split('\n')
    required_headers = {'concepto', 'fecha', 'importe'}
    
    for i, line in enumerate(lines):
        if not line.strip():
            continue
            
        # Split by delimiter and normalize
        columns = [col.strip().lower() for col in line.split(delimiter)]
        
        # Check if this row contains all required headers
        found_headers = set()
        for col in columns:
            for req in required_headers:
                if req in col:
                    found_headers.add(req)
        
        if required_headers.issubset(found_headers):
            # Return original column names (not lowercased)
            original_columns = [col.strip() for col in line.split(delimiter)]
            return i, original_columns
    
    return -1, []


def parse_pdf_file(file: Union[BytesIO, str]) -> pd.DataFrame:
    """
    Parse a Trade Republic style PDF bank statement.
    
    Extracts transaction table processing:
    - FECHA (Date)
    - DESCRIPCIÓN (Description -> Concepto)
    - ENTRADA DE DINERO (Income)
    - SALIDA DE DINERO (Expense)
    
    Args:
        file: PDF file path or object
        
    Returns:
        DataFrame with standardized columns
    """
    all_rows = []
    
    try:
        # Open PDF (handle both path string and file object)
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                # Extract tables using default settings which usually work well for grid-like tables
                tables = page.extract_tables()
                
                for table in tables:
                    if not table:
                        continue
                        
                    # Find header row
                    header_idx = -1
                    headers = []
                    
                    for i, row in enumerate(table):
                        # Filter None values and convert to string
                        row_text = [str(cell).strip().upper() for cell in row if cell is not None]
                        
                        # Check for key columns
                        if 'FECHA' in row_text and ('DESCRIPCIÓN' in row_text or 'DESCRIPTION' in row_text):
                            header_idx = i
                            headers = row_text
                            break
                    
                    if header_idx != -1:
                        # Process data rows
                        for row in table[header_idx + 1:]:
                            # Skip empty rows
                            if not any(row):
                                continue
                                
                            row_data = {}
                            # Map columns based on position
                            for col_idx, cell in enumerate(row):
                                if col_idx < len(headers):
                                    header = headers[col_idx]
                                    val = str(cell).strip() if cell else ""
                                    
                                    if header == 'FECHA':
                                        row_data['Fecha'] = val
                                    elif header in ['DESCRIPCIÓN', 'DESCRIPTION']:
                                        row_data['Concepto'] = val
                                    elif 'ENTRADA' in header:
                                        row_data['Income'] = val
                                    elif 'SALIDA' in header:
                                        row_data['Expense'] = val
                            
                            # Only add if we have basic data
                            if 'Fecha' in row_data and 'Concepto' in row_data:
                                all_rows.append(row_data)

    except Exception as e:
        raise ValueError(f"Error parsing PDF: {str(e)}")
        
    if not all_rows:
        return pd.DataFrame()
        
    # Convert to DataFrame
    df = pd.DataFrame(all_rows)
    
    # Calculate Importe (Amount) from Income/Expense
    def calculate_amount(row):
        income = preprocess_amount(row.get('Income', '0'))
        expense = preprocess_amount(row.get('Expense', '0'))
        
        if income > 0:
            return income
        elif expense > 0:
            # Expense column is usually positive number representing outflow
            return -expense
        else:
            return 0.0
            
    df['Importe'] = df.apply(calculate_amount, axis=1)
    
    # Clean up Date (Trade Republic format like "01 dic 2025")
    # We might need to handle Spanish month names
    spanish_months = {
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
    }
    
    def parse_tr_date(date_str):
        if not date_str:
            return None
            
        parts = date_str.split()
        if len(parts) == 3:
            day, month_str, year = parts
            month = spanish_months.get(month_str.lower()[:3], '01')
            return f"{day}/{month}/{year}"
        return date_str

    if 'Fecha' in df.columns:
        df['Fecha'] = df['Fecha'].apply(parse_tr_date)
        
    return df


def parse_bank_file(file: Union[BytesIO, str]) -> pd.DataFrame:
    """
    Parse a bank statement file (CSV or Excel) with dynamic header detection.
    
    Handles Imagin Bank format with metadata headers by scanning for the
    actual data header row containing 'Concepto', 'Fecha', 'Importe'.
    
    Args:
        file: File object or path
        
    Returns:
        DataFrame with raw bank data (only valid transaction rows)
    """
    # Try to determine file type
    filename = ""
    if hasattr(file, 'name'):
        filename = file.name.lower()
    elif isinstance(file, str):
        filename = file.lower()
    
    try:
        if filename.endswith('.pdf'):
            df = parse_pdf_file(file)
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            # For Excel, try to find header row
            df = pd.read_excel(file, header=None)
            # Convert to CSV-like format to use same header detection logic
            content = df.to_csv(sep=';', index=False, header=False)
            header_row, columns = find_header_row(content, ';')
            
            if header_row >= 0:
                df = pd.read_excel(file, skiprows=header_row, header=0)
            else:
                df = pd.read_excel(file)
        else:
            # CSV with semicolon delimiter
            if hasattr(file, 'read'):
                content = file.read()
                if isinstance(content, bytes):
                    # Try different encodings
                    for encoding in ['utf-8', 'latin-1', 'cp1252']:
                        try:
                            content = content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        content = content.decode('utf-8', errors='replace')
            else:
                with open(file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            
            # Find the header row dynamically
            header_row, columns = find_header_row(content, ';')
            
            if header_row >= 0:
                # Read CSV starting from header row
                df = pd.read_csv(
                    StringIO(content), 
                    sep=';', 
                    skiprows=header_row,
                    header=0,
                    on_bad_lines='skip'  # Skip malformed rows
                )
            else:
                # Fall back to reading from start
                df = pd.read_csv(
                    StringIO(content), 
                    sep=';', 
                    encoding='utf-8',
                    on_bad_lines='skip'
                )
                
    except Exception as e:
        raise ValueError(f"Error parsing file: {str(e)}")
    
    # Standardize column names (handle variations)
    column_mapping = {}
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if 'concepto' in col_lower or 'concept' in col_lower or 'description' in col_lower:
            column_mapping[col] = 'Concepto'
        elif 'tarjeta' in col_lower or 'card' in col_lower:
            column_mapping[col] = 'Tarjeta'
        elif 'fecha' in col_lower or 'date' in col_lower:
            column_mapping[col] = 'Fecha'
        elif 'importe' in col_lower or 'amount' in col_lower or 'cantidad' in col_lower:
            column_mapping[col] = 'Importe'
    
    df = df.rename(columns=column_mapping)
    
    # Ensure required columns exist
    required_columns = ['Concepto', 'Importe']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}. Found columns: {list(df.columns)}")
    
    # Clean up: remove rows where Concepto is empty or NaN
    df = df.dropna(subset=['Concepto'])
    df = df[df['Concepto'].astype(str).str.strip() != '']
    
    return df


def process_dataframe(df: pd.DataFrame, learned_mappings: dict) -> pd.DataFrame:
    """
    Full preprocessing pipeline for bank statement data.
    
    1. Clean and strip Concepto values
    2. Convert amounts to float (handles Spanish format)
    3. Parse dates (DD/MM/YYYY format)
    4. Auto-categorize using learned mappings and keyword patterns
    5. Filter out invalid rows silently
    
    Args:
        df: Raw DataFrame from parse_bank_file
        learned_mappings: Dict of concept -> category from user corrections
        
    Returns:
        Processed DataFrame with Amount, Date, and Category columns
    """
    # Create a copy to avoid modifying original
    processed = df.copy()
    
    # Clean Concepto - strip whitespace
    if 'Concepto' in processed.columns:
        processed['Concepto'] = processed['Concepto'].astype(str).str.strip()
        # Remove rows with empty Concepto
        processed = processed[processed['Concepto'] != '']
        processed = processed[processed['Concepto'].str.lower() != 'nan']
    
    # Convert amounts
    if 'Importe' in processed.columns:
        processed['Amount'] = processed['Importe'].apply(preprocess_amount)
        # Filter out rows where amount is 0 and original was not "0"
        # Keep rows where amount conversion was successful
    else:
        processed['Amount'] = 0.0
    
    # Parse dates
    if 'Fecha' in processed.columns:
        processed['Date'] = processed['Fecha'].apply(parse_date)
    else:
        processed['Date'] = None
    
    # Auto-categorize:
    # 1. Positive amounts (income) are auto-assigned to "Income" category
    # 2. Negative amounts (expenses) use learned mappings and keyword patterns
    def categorize_row(row):
        amount = row.get('Amount', 0)
        concept = str(row.get('Concepto', '')).strip()
        
        # Positive amounts are income, not expenses
        if amount > 0:
            return "Income"
        
        # For expenses, use the normal categorization
        return categorize_concept(concept, learned_mappings)
    
    processed['Category'] = processed.apply(categorize_row, axis=1)
    
    # Add flag for rows needing attention (only expenses without category)
    processed['NeedsReview'] = (processed['Category'].isna()) & (processed['Amount'] < 0)
    
    # Filter out completely invalid rows (no amount and no date)
    # But keep rows that might just be missing a date
    valid_mask = (processed['Amount'] != 0) | (processed['Date'].notna())
    processed = processed[valid_mask]
    
    # Reset index after filtering
    processed = processed.reset_index(drop=True)
    
    return processed


def get_month_year_from_data(df: pd.DataFrame) -> str:
    """
    Extract month-year string from data for file naming.
    
    Args:
        df: Processed DataFrame with Date column
        
    Returns:
        String like "2024-01" or "unknown" if no dates
    """
    if 'Date' not in df.columns:
        return "unknown"
    
    valid_dates = df['Date'].dropna()
    if valid_dates.empty:
        return "unknown"
    
    # Use the most common month in the data
    months = valid_dates.apply(lambda x: x.strftime('%Y-%m') if isinstance(x, datetime) else None)
    months = months.dropna()
    
    if months.empty:
        return "unknown"
    
    return months.mode().iloc[0] if not months.empty else "unknown"
