import os, json
from main import GUILD_FILE

def load_guild_data():
    if not os.path.exists(GUILD_FILE):
        return {}
    with open(GUILD_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_guild_data(data):
    with open(GUILD_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_guild_config(guild_id: str) -> dict:
    data = load_guild_data()
    default_config = {
        "welcome_channel_id": None,
        "goodbye_channel_id": None,
        "ghost_ping_enabled": False,
        "edit_delete_history_enabled": True,
        "level_up_message_enabled": False,
        "counter_channels": {}
    }

    if guild_id not in data:
        data[guild_id] = default_config
    else:
        for key, value in default_config.items():
            if key not in data[guild_id]:
                data[guild_id][key] = value
    save_guild_data(data)
    return data[guild_id], data


def get_guild_data(data, guild_id):
    if guild_id not in data:
        data[guild_id] = {
            "users": {},
            "shop": {},
            "recipes": {},
            "item_uses": {},
            "item_values": {}
        }
    return data[guild_id]