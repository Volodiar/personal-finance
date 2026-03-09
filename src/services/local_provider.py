import pandas as pd
from typing import List, Dict, Optional, Tuple
from services.data_interface import DataProvider
import user_manager
import storage

class LocalDataProvider(DataProvider):
    """
    Implementation of DataProvider for Local Storage (CSV/JSON).
    """

    def get_users(self) -> List[Dict]:
        return user_manager.load_users()

    def get_user_by_name(self, name: str) -> Optional[Dict]:
        return user_manager.get_user_by_name(name)

    def add_user(self, name: str, emoji: str, email: str = None) -> bool:
        # Local mode doesn't really use email for auth, but we accept it for interface compatibility
        return user_manager.add_user(name, emoji)

    def update_user(self, old_name: str, new_name: str = None, new_emoji: str = None) -> bool:
        return user_manager.update_user(old_name, new_name, new_emoji)

    def delete_user(self, name: str) -> bool:
        return user_manager.delete_user(name)

    def get_current_user_email(self) -> Optional[str]:
        # Local mode implies "admin" or single local user context, no OAuth usually.
        return None

    def load_transactions(self, user_name: str) -> pd.DataFrame:
        return storage.load_user_data(user_name)

    def save_transactions(self, user_name: str, df: pd.DataFrame) -> bool:
        # storage.save_user_data returns path string on success
        result = storage.save_user_data(user_name, df)
        return bool(result) and "Error" not in result

    def add_transactions(self, user_name: str, new_df: pd.DataFrame) -> Tuple[int, int, int]:
        # storage.add_transactions returns (filepath, new, dup, updated)
        _, new, dup, updated = storage.add_transactions(user_name, new_df)
        return new, dup, updated

    def get_all_users_transactions(self) -> Dict[str, pd.DataFrame]:
        # Maps keys to lower case in original storage, we might want to standardize
        # The interface expects Dict[str, DataFrame]
        return storage.load_all_data()
