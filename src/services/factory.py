import streamlit as st
from services.data_interface import DataProvider
from services.local_provider import LocalDataProvider
from services.cloud_provider import CloudDataProvider

def get_data_provider() -> DataProvider:
    """
    Factory method to get the active DataProvider.
    Determines Local vs Cloud based on secrets configuration.
    """
    # Check if cloud is configured
    try:
        is_cloud = bool(st.secrets.get("gcp_service_account"))
    except FileNotFoundError:
        is_cloud = False
    except Exception:
        is_cloud = False

    if is_cloud:
        return CloudDataProvider()
    else:
        return LocalDataProvider()
