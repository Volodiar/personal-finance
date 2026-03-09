from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
import pandas as pd
from datetime import datetime

class DataProvider(ABC):
    """
    Abstract Base Class for Data Persistence.
    Standardizes operations across Local (CSV) and Cloud (Sheets) storage.
    """

    # --- User Management ---

    @abstractmethod
    def get_users(self) -> List[Dict]:
        """Retrieve list of all registered users."""
        pass

    @abstractmethod
    def get_user_by_name(self, name: str) -> Optional[Dict]:
        """Retrieve a specific user by display name."""
        pass

    @abstractmethod
    def add_user(self, name: str, emoji: str, email: str = None) -> bool:
        """Create a new user profile."""
        pass

    @abstractmethod
    def update_user(self, old_name: str, new_name: str = None, new_emoji: str = None) -> bool:
        """Update an existing user's profile."""
        pass

    @abstractmethod
    def delete_user(self, name: str) -> bool:
        """Delete a user and their associated data."""
        pass
    
    @abstractmethod
    def get_current_user_email(self) -> Optional[str]:
        """Get the email of the currently authenticated user (for cloud contexts)."""
        pass

    # --- Transaction Management ---

    @abstractmethod
    def load_transactions(self, user_name: str) -> pd.DataFrame:
        """Load all transactions for a specific user."""
        pass

    @abstractmethod
    def save_transactions(self, user_name: str, df: pd.DataFrame) -> bool:
        """Save (overwrite) transactions for a specific user."""
        pass

    @abstractmethod
    def add_transactions(self, user_name: str, new_df: pd.DataFrame) -> Tuple[int, int, int]:
        """
        Merge and add new transactions.
        Returns: (new_count, duplicate_count, updated_count)
        """
        pass
    
    @abstractmethod
    def get_all_users_transactions(self) -> Dict[str, pd.DataFrame]:
        """Load transactions for ALL users (for joint analytics)."""
        pass
