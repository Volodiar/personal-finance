import pandas as pd
from typing import List, Dict, Optional, Tuple
from services.data_interface import DataProvider
import sheets_storage
import accounts
import auth
import user_manager # We still need this for some helper logic or we duplicate it? 
# Actually, we should try to use the sheets/accounts modules directly if possible, 
# but user_manager has some good cloud logic mixed in we can extract/reuse.

class CloudDataProvider(DataProvider):
    """
    Implementation of DataProvider for Google Sheets Storage.
    """

    def _get_account_hash(self) -> Optional[str]:
        email = self.get_current_user_email()
        if not email:
            return None
        return accounts.get_account_hash(email)

    def get_users(self) -> List[Dict]:
        email = self.get_current_user_email()
        if not email:
            return []
        
        data_users = accounts.get_data_users(email)
        # Map to standard format
        return [
            {
                "name": du['name'],
                "folder": du['id'],
                "emoji": du['emoji'],
                "created": du.get('created')
            }
            for du in data_users
        ]

    def get_user_by_name(self, name: str) -> Optional[Dict]:
        users = self.get_users()
        for u in users:
            if u["name"].lower() == name.lower():
                return u
        return None

    def add_user(self, name: str, emoji: str, email: str = None) -> bool:
        current_email = self.get_current_user_email()
        if not current_email:
            return False
        return accounts.add_data_user(current_email, name, emoji)

    def update_user(self, old_name: str, new_name: str = None, new_emoji: str = None) -> bool:
        current_email = self.get_current_user_email()
        if not current_email:
            return False
        
        user = self.get_user_by_name(old_name)
        if not user:
            return False
            
        return accounts.update_data_user(current_email, user['folder'], new_name, new_emoji)

    def delete_user(self, name: str) -> bool:
        current_email = self.get_current_user_email()
        if not current_email:
            return False
            
        user = self.get_user_by_name(name)
        if not user:
            return False
            
        return accounts.delete_data_user(current_email, user['folder'])

    def get_current_user_email(self) -> Optional[str]:
        user = auth.get_current_user()
        return user.get('email') if user else None

    def load_transactions(self, user_name: str) -> pd.DataFrame:
        account_hash = self._get_account_hash()
        if not account_hash:
            return pd.DataFrame()
            
        user = self.get_user_by_name(user_name)
        # Fallback to name-based ID if user not found (legacy compat)
        user_id = user['folder'] if user else user_name.lower().replace(' ', '_')
        
        return sheets_storage.load_data_user_transactions(account_hash, user_id)

    def save_transactions(self, user_name: str, df: pd.DataFrame) -> bool:
        account_hash = self._get_account_hash()
        if not account_hash:
            return False
            
        user = self.get_user_by_name(user_name)
        user_id = user['folder'] if user else user_name.lower().replace(' ', '_')
        
        return sheets_storage.save_data_user_transactions(account_hash, user_id, df)

    def add_transactions(self, user_name: str, new_df: pd.DataFrame) -> Tuple[int, int, int]:
        account_hash = self._get_account_hash()
        if not account_hash:
            return 0, 0, 0
            
        user = self.get_user_by_name(user_name)
        user_id = user['folder'] if user else user_name.lower().replace(' ', '_')
        
        result = sheets_storage.add_transactions(account_hash, user_id, new_df)
        
        # Cloud add_transactions doesn't currently return 'updated_count', so we default to 0
        return result.get('added', 0), result.get('duplicates', 0), 0

    def get_all_users_transactions(self) -> Dict[str, pd.DataFrame]:
        email = self.get_current_user_email()
        if not email:
            return {}
            
        account_hash = accounts.get_account_hash(email)
        data_users = accounts.get_data_users(email)
        
        # Convert to tuple of tuples for hashability (cache_data requirement)
        data_users_tuple = tuple(tuple(sorted(du.items())) for du in data_users)
        
        return sheets_storage.load_all_data_users_transactions(account_hash, data_users_tuple)
