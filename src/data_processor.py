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
import streamlit as st # For debugging

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
    Parse a Trade Republic style PDF bank statement using text layout analysis.
    
    Uses extracts_words to determine column positions dynamically based on headers.
    """
    all_rows = []
    
    try:
        with pdfplumber.open(file) as pdf:
            st.write(f"DEBUG: Processing PDF with {len(pdf.pages)} pages")
            
            # Store coordinates from first page to use on subsequent pages
            last_header_coords = None
            
            for page_num, page in enumerate(pdf.pages):
                width = page.width
                words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False)
                
                # 1. Detect Header Positions
                header_y = -1
                
                # Search for key headers
                found_headers = {}
                for w in words:
                    text = w['text'].upper()
                    if 'ENTRADA' in text:
                        found_headers['income'] = w
                    elif 'SALIDA' in text:
                        found_headers['expense'] = w
                    elif 'BALANCE' in text or 'SALDO' in text:
                        # Trade Republic uses "BALANCE" in the table
                        found_headers['balance'] = w
                    elif 'FECHA' in text:
                        found_headers['date'] = w
                
                if 'income' in found_headers and 'expense' in found_headers:
                    # Define column boundaries
                    header_y = found_headers['income']['top']
                    
                    # Columns ranges (x0)
                    x_income = found_headers['income']['x0'] - 20 # buffer
                    x_expense = found_headers['expense']['x0'] - 20
                    # Handle missing balance header gracefully if needed, though usually present
                    x_balance = found_headers['balance']['x0'] - 20 if 'balance' in found_headers else width
                    
                    last_header_coords = {
                        'x_income': x_income,
                        'x_expense': x_expense,
                        'x_balance': x_balance
                    }
                    
                    st.write(f"DEBUG: Page {page_num+1} Headers found at Y={header_y:.2f}. "
                             f"X-Coords: Income={x_income:.2f}, Expense={x_expense:.2f}, Balance={x_balance:.2f}")

                elif last_header_coords:
                    # Use coordinates from previous page
                    x_income = last_header_coords['x_income']
                    x_expense = last_header_coords['x_expense']
                    x_balance = last_header_coords['x_balance']
                    st.write(f"DEBUG: Page {page_num+1} using inherited headers. X-Coords: Income={x_income:.2f}")
                    # Assume no header processing needed, start near top
                    header_y = 50 
                else:
                    st.warning(f"DEBUG: Page {page_num+1} - Could not find headers (ENTRADA/SALIDA) and no previous headers. Skipping page.")
                    continue

                # 2. Group words by line (using top coordinate)
                # Sort by top first
                words_sorted = sorted(words, key=lambda w: w['top'])
                
                lines = []
                current_line = []
                current_top = -1
                
                for w in words_sorted:
                    # Skip headers and above
                    if w['top'] <= header_y + 10:
                        continue
                        
                    if current_top == -1:
                        current_top = w['top']
                        current_line.append(w)
                    else:
                        if abs(w['top'] - current_top) < 5: # Same line tolerance
                            current_line.append(w)
                        else:
                            lines.append(current_line)
                            current_line = [w]
                            current_top = w['top']
                if current_line:
                    lines.append(current_line)
                
                # 3. Process Lines
                st.write(f"DEBUG: Page {page_num+1} - Processing {len(lines)} detected lines")
                
                for line in lines:
                    # Sort words in line by x0
                    line = sorted(line, key=lambda w: w['x0'])
                    line_text = " ".join([w['text'] for w in line])
                    
                    # Must start with a date-like pattern to be a transaction
                    # Regex: 2 digits, space, 3 chars, space, 4 digits
                    import re
                    first_word = line[0]['text']
                    if not re.match(r'^\d{2}$', first_word):
                         continue
                         
                    # Attempt to identify components based on X coordinates
                    date_parts = []
                    concept_parts = []
                    income_val = None
                    expense_val = None
                    
                    for w in line:
                        cx = w['x0']
                        text = w['text']
                        
                        if cx < x_income:
                            # Date + Description area
                            concept_parts.append(text)
                        
                        elif cx >= x_income and cx < x_expense:
                            if re.search(r'\d', text): # Contains number
                                income_val = text
                        
                        elif cx >= x_expense and cx < x_balance:
                            if re.search(r'\d', text):
                                expense_val = text
                                
                    # Attempt to extract date from the beginning of the concept parts
                    full_text = " ".join(concept_parts)
                    date_str = ""
                    concept_str = full_text
                    
                    # Regex for "DD MMM YYYY" (e.g., "01 dic 2025")
                    # Spanish months are 3 chars
                    date_match = re.match(r'^(\d{2}\s+[a-zA-Z]{3}\s+\d{4})\s+(.*)', full_text)
                    
                    if date_match:
                        date_str = date_match.group(1)
                        concept_str = date_match.group(2)
                    else:
                        # Fallback: Maybe just "DD MMM" or other formats?
                        # For now, if we match the start, we take it.
                        match_simple = re.match(r'^(\d{2}\s+[a-zA-Z]{3})\s+(.*)', full_text) # Missing year?
                        if match_simple:
                           # This might be risky if year is on next line or missing
                           pass
                    
                    # Basic validation: needs date
                    if not date_str:
                         st.write(f"DEBUG: Skipping line (No Date): {full_text}")
                         continue

                    # Clean amount strings
                    def clean_amt(s):
                        if not s: return 0.0
                        return preprocess_amount(s)

                    amount = 0.0
                    if income_val:
                        amount = clean_amt(income_val)
                    elif expense_val:
                        amount = -clean_amt(expense_val) # Expenses are negative in our system
                    
                    if amount != 0:
                        all_rows.append({
                            'Fecha': date_str,
                            'Concepto': concept_str,
                            'Importe': amount,
                            'Income': income_val, # Keep raw for debug if needed
                            'Expense': expense_val
                        })
                        st.write(f"DEBUG: Extracted -> Date: {date_str} | Concept: {concept_str} | Amount: {amount}")

    except Exception as e:
        import traceback
        st.error(f"Error parsing PDF: {str(e)}")
        st.code(traceback.format_exc())
        
    if not all_rows:
        return pd.DataFrame()
        
    # Convert to DataFrame
    df = pd.DataFrame(all_rows)
    
    # Clean up Date (Trade Republic format like "01 dic 2025")
    # We might need to handle Spanish month names
    spanish_months = {
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12',
        'jan': '01', 'dec': '12', 'apr': '04', 'aug': '08' # English fallbacks just in case
    }
    
    def parse_tr_date(date_str):
        if not date_str:
            return None
        
        # Remove any leading/trailing junk
        date_str = date_str.strip()
        
        parts = date_str.split()
        if len(parts) >= 3:
            day = parts[0]
            month_str = parts[1].lower()
            year = parts[2]
            
            # Remove dots if any (sept.)
            month_str = month_str.replace('.', '')
            
            month = spanish_months.get(month_str[:3], '01')
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
