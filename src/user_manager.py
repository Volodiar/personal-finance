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
    """Load all users from users.json or detect from folder structure."""
    ensure_data_dir()
    
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("users", [])
    
    # If no users.json, detect from existing folders
    users = []
    for item in DATA_DIR.iterdir():
        if item.is_dir() and (item / "transactions.csv").exists():
            users.append({
                "name": item.name.capitalize(),
                "folder": item.name,
                "emoji": "👤",
                "created": datetime.now().isoformat()
            })
    
    if users:
        save_users(users)
    
    return users


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
