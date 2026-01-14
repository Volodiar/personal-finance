"""
user_manager.py - Dynamic user management.

Handles user creation, deletion, and detection from folder structure.
Users are stored in /data/users.json with their profile info.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st # for session state access
import sys

# Import components
# Using import inside functions or try/except to avoid circular imports if strictly necessary, 
# but top level should be fine if architecture is clean.
# However, user_manager is imported by app.py, which imports auth/accounts.
# Let's use lazy imports inside functions for safety against circular deps with App structure.


# User data paths
DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"

# Available emojis for user selection
AVAILABLE_EMOJIS = [
    "👤", "👩", "👨", "👧", "👦", "🧑", "👵", "👴",
    "🙋", "🙋‍♀️", "🙋‍♂️", "💁", "💁‍♀️", "💁‍♂️",
    "🧔", "👱", "👱‍♀️", "👱‍♂️", "🧓", "👶",
    "🦸", "🦸‍♀️", "🦸‍♂️", "🧙", "🧙‍♀️", "🧙‍♂️",
    "🐱", "🐶", "🦊", "🐼", "🐨", "🦁", "🐯", "🐻",
    "🌟", "⭐", "🌙", "☀️", "🌈", "💫", "✨", "🎯"
]


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_users() -> List[Dict]:
    """Load all users from users.json, local folders, or Cloud Account."""
    from sheets_storage import is_cloud_mode
    
    if is_cloud_mode():
        # CLOUD MODE: Get users from Google Sheet
        from auth import get_current_user
        from accounts import get_data_users
        
        # We need the current logged-in user's email to find their account
        current_user = get_current_user()
        email = current_user.get('email')
        
        if not email:
            # If not logged in, we can't show users yet
            return []
            
        # Fetch data users from the "accounts" sheet
        data_users = get_data_users(email)
        
        # Map to user_manager format
        users = []
        for du in data_users:
            users.append({
                "name": du['name'],
                "folder": du['id'], # In cloud mode, folder = data_user_id
                "emoji": du['emoji'],
                "created": du.get('created', datetime.now().isoformat())
            })
        return users
        
    else:
        # LOCAL MODE (Existing Logic)
        ensure_data_dir()
        
        existing_users = []
        if USERS_FILE.exists():
            try:
                with open(USERS_FILE, 'r') as f:
                    existing_users = json.load(f).get("users", [])
            except json.JSONDecodeError:
                existing_users = []
                
        # Always detect from folders to catch new users (like "TEST" created via upload)
        folder_users = []
        existing_folders = {u["folder"].lower() for u in existing_users}
        existing_names = {u["name"].lower() for u in existing_users}
        
        dirty = False
        
        # Check data directory for user folders
        if DATA_DIR.exists():
            for item in DATA_DIR.iterdir():
                # Check if it's a directory and has a transactions file or just is a user folder
                if item.is_dir() and not item.name.startswith('.'):
                    folder_name = item.name.lower()
                    
                    # specific check for transactions.csv to confirm it's a user folder
                    if (item / "transactions.csv").exists():
                        if folder_name not in existing_folders:
                            # Infer name from folder
                            display_name = item.name.replace('_', ' ').title()
                            
                            # Avoid name collision if folder is different but name exists
                            if display_name.lower() in existing_names:
                                 # Should rarely happen, but just in case
                                 continue
                                 
                            new_user = {
                                "name": display_name,
                                "folder": item.name, # Keep original case of folder if needed, or use folder_name
                                "emoji": "👤",
                                "created": datetime.now().isoformat()
                            }
                            existing_users.append(new_user)
                            existing_folders.add(folder_name)
                            dirty = True
        
        if dirty:
            save_users(existing_users)
        
        return existing_users


def save_users(users: List[Dict]):
    """Save users list to users.json."""
    ensure_data_dir()
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": users}, f, indent=2)


def get_user_names() -> List[str]:
    """Get list of user names."""
    return [u["name"] for u in load_users()]


def get_user_by_name(name: str) -> Optional[Dict]:
    """Get user by name (case-insensitive)."""
    for user in load_users():
        if user["name"].lower() == name.lower():
            return user
    return None


def get_user_folder(name: str) -> str:
    """Get folder name for a user."""
    user = get_user_by_name(name)
    return user["folder"] if user else name.lower()


def add_user(name: str, emoji: str) -> bool:
    """
    Add a new user.
    
    Args:
        name: User display name
        emoji: User emoji icon
        
    Returns:
        True if successful, False if user already exists
    """
    from sheets_storage import is_cloud_mode
    
    if is_cloud_mode():
        # CLOUD MODE
        from auth import get_current_user
        from accounts import add_data_user as add_cloud_user
        
        current_email = get_current_user().get('email')
        if not current_email:
            return False
            
        return add_cloud_user(current_email, name, emoji)
            
    else:
        # LOCAL MODE
        users = load_users()
        
        # Check if user already exists
        if any(u["name"].lower() == name.lower() for u in users):
            return False
        
        folder_name = name.lower().replace(" ", "_")
        
        # Create user folder
        user_folder = DATA_DIR / folder_name
        user_folder.mkdir(parents=True, exist_ok=True)
        
        # Add to users list
        users.append({
            "name": name,
            "folder": folder_name,
            "emoji": emoji,
            "created": datetime.now().isoformat()
        })
        
        save_users(users)
        return True


def delete_user(name: str) -> bool:
    """
    Delete a user and their data folder.
    
    Args:
        name: User display name
        
    Returns:
        True if successful
    """
    from sheets_storage import is_cloud_mode
    
    if is_cloud_mode():
        # CLOUD MODE
        from auth import get_current_user
        from accounts import delete_data_user as delete_cloud_user
        
        current_email = get_current_user().get('email')
        if not current_email:
            return False
            
        # Need user ID from name
        user = get_user_by_name(name)
        if not user:
            return False
            
        return delete_cloud_user(current_email, user['folder']) # folder holds the ID in data
        
    else:
        # LOCAL MODE
        users = load_users()
        user = get_user_by_name(name)
        
        if not user:
            return False
        
        # Remove user folder
        user_folder = DATA_DIR / user["folder"]
        if user_folder.exists():
            shutil.rmtree(user_folder)
        
        # Remove from users list
        users = [u for u in users if u["name"].lower() != name.lower()]
        save_users(users)
        
        return True


def update_user(old_name: str, new_name: str = None, new_emoji: str = None) -> bool:
    """Update user name or emoji."""
    from sheets_storage import is_cloud_mode
    
    if is_cloud_mode():
         # CLOUD MODE
        from auth import get_current_user
        from accounts import update_data_user as update_cloud_user
        
        current_email = get_current_user().get('email')
        if not current_email:
            return False
            
        user = get_user_by_name(old_name)
        if not user:
            return False
            
        return update_cloud_user(current_email, user['folder'], new_name, new_emoji)
        
    else:
        # LOCAL MODE
        users = load_users()
        
        for user in users:
            if user["name"].lower() == old_name.lower():
                if new_name:
                    user["name"] = new_name
                if new_emoji:
                    user["emoji"] = new_emoji
                save_users(users)
                return True
        
        return False


def get_user_count() -> int:
    """Get number of users."""
    return len(load_users())


def should_show_joint_view() -> bool:
    """Return True if joint view should be available (2+ users)."""
    return get_user_count() > 1


def get_user_by_folder(folder: str) -> Optional[Dict]:
    """Get user by folder name."""
    for user in load_users():
        if user["folder"] == folder:
            return user
    return None


def get_or_create_user_from_email(email: str, name: str = None) -> Dict:
    """
    Get or create a user based on their email.
    Used for OAuth login to auto-create users.
    
    Args:
        email: User's email address
        name: User's display name (from OAuth)
        
    Returns:
        User dict with name, folder, emoji
    """
    # Convert email to folder name
    folder = email.split("@")[0].replace(".", "_").replace("-", "_").lower()
    folder = "".join(c for c in folder if c.isalnum() or c == "_")
    
    # Check if user already exists
    existing = get_user_by_folder(folder)
    if existing:
        return existing
    
    # Create new user
    display_name = name or email.split("@")[0].replace(".", " ").title()
    
    users = load_users()
    new_user = {
        "name": display_name,
        "folder": folder,
        "emoji": "👤",
        "email": email,
        "created": datetime.now().isoformat()
    }
    
    users.append(new_user)
    save_users(users)
    
    # Create user folder (for local dev)
    user_folder = DATA_DIR / folder
    user_folder.mkdir(parents=True, exist_ok=True)
    
    return new_user

