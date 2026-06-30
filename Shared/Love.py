import os, json
from main import LOVE_FILE

def load_love_data():
    if not os.path.exists(LOVE_FILE):
        with open(LOVE_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(LOVE_FILE, "r") as f:
        return json.load(f)


def save_love_data(data):
    with open(LOVE_FILE, "w") as f:
        json.dump(data, f, indent=4)