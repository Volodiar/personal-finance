
import sys
import os
from unittest.mock import MagicMock, patch
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Mock streamlit before importing modules that use it
sys.modules['streamlit'] = MagicMock()
import streamlit as st
st.secrets = {"gcp_service_account": {"mock": "true"}} # Simulate cloud mode

# Import sheets_storage
import sheets_storage

def test_worksheet_naming():
    print("Testing worksheet naming logic...")
    
    account_hash = "abcdef12"
    
    # Case 1: ID passed (lowercase)
    case1 = sheets_storage.get_worksheet_name(account_hash, "pablo")
    print(f"Input 'pablo' -> Worksheet: '{case1}'")
    
    # Case 2: Name passed (Title Case)
    case2 = sheets_storage.get_worksheet_name(account_hash, "Pablo")
    print(f"Input 'Pablo' -> Worksheet: '{case2}'")
    
    if case1 != case2:
        print("\nFAILURE: sheets_storage does NOT normalize casing. 'pablo' and 'Pablo' produce DIFFERENT sheets.")
    else:
        print("\nSUCCESS: sheets_storage normalizes casing.")

if __name__ == "__main__":
    test_worksheet_naming()
