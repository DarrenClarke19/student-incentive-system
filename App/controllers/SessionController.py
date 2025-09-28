import json
import os
from datetime import datetime
from functools import wraps
from App.models import User

# Session management using a file
SESSION_FILE = ".current_user.json"

def set_current_user(user):
    session_data = {
        "username": user.username,
        "role": user.role.value,
        "user_id": user.id,
        "login_time": datetime.utcnow().isoformat()
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f)

def get_current_user():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def clear_current_user():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def login(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        set_current_user(user)
        return {
            "success": True,
            "message": f"Logged in as {username} ({user.role.value})"
        }
    else:
        return {
            "success": False,
            "message": "Invalid username or password"
        }

def logout():
    clear_current_user()
    return {
        "success": True,
        "message": "Logged out"
    }

def get_current_user_info():
    user = get_current_user()
    if user:
        return {
            "success": True,
            "message": f"Logged in as: {user['username']} ({user['role']})"
        }
    else:
        return {
            "success": False,
            "message": "Not logged in"
        }

def require_login():
    user = get_current_user()
    if not user:
        return {
            "success": False,
            "message": "You must login first. Use: flask auth login <username>",
            "user": None
        }
    return {
        "success": True,
        "message": "User is logged in",
        "user": user
    }

def require_role(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            login_result = require_login()
            if not login_result["success"]:
                return login_result
            
            user = login_result["user"]
            if user["role"] not in allowed_roles:
                return {
                    "success": False,
                    "message": f"Insufficient permissions. Required role: {', '.join(allowed_roles)}",
                    "user": None
                }
            
            return func(*args, **kwargs)
        return wrapper
    return decorator