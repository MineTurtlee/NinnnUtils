from main import LOCK_CONFIG_FILE
import os, json

def load_lock_config():
    if not os.path.exists(LOCK_CONFIG_FILE):
        return {}, {}
    with open(LOCK_CONFIG_FILE, 'r') as f:
        try:
            data = json.load(f)
            locked = {int(k): v for k, v in data.get("locked_channels", {}).items()}
            admin = {int(k): v for k, v in data.get("admin_log_channels", {}).items()}
            return locked, admin
        except (json.JSONDecodeError, ValueError):
            return {}, {}


def save_lock_config(locked, admin):
    with open(LOCK_CONFIG_FILE, 'w') as f:
        json.dump({"locked_channels": locked, "admin_log_channels": admin}, f, indent=4)