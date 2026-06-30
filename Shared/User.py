import json, os
from main import USER_FILE
from discord.abc import User
from discord import Member
from .Guild import *
from .Inventory import *

def get_user_color(user_id: str) -> str:
    settings = load_user_settings()
    return get_user_settings_entry(settings, user_id).get("color", "white")

def get_user_data(data, guild_id, user_id):
    guild = get_guild_data(data, guild_id)
    user_id = str(user_id)
    if user_id not in guild["users"]:
        guild["users"][user_id] = {"balance": 0, "inventory": {}}
    migrate_inventory(guild["users"][user_id])
    return guild["users"][user_id]

def load_user_settings():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_user_settings(data):
    with open(USER_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def get_user_settings_entry(settings: dict, user_id: str) -> dict:
    if "users" not in settings or not isinstance(settings["users"], dict):
        settings["users"] = {}

    user_key = str(user_id)
    user_settings = settings["users"].get(user_key)
    if not isinstance(user_settings, dict):
        user_settings = {}
        settings["users"][user_key] = user_settings

    return user_settings

def get_user_pings_enabled(user_id: str) -> bool:
    settings = load_user_settings()
    return get_user_settings_entry(settings, user_id).get("user_pings", True)


def format_user_reference(user: User | Member, settings: dict | None = None) -> str:
    if settings is None:
        settings = load_user_settings()

    if get_user_settings_entry(settings, user.id).get("user_pings", True):
        return user.mention

    return getattr(user, "display_name", getattr(user, "name", str(user)))


def get_banner_name(member: User | Member) -> str:
    display_name = member.display_name
    if any(ord(char) > 127 for char in display_name):
        return member.name
    return display_name


def format_banner_username(name: str, limit: int = 17) -> str:
    if len(name) <= limit:
        return name
    return name[:limit] + "..."