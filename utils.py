import json
import os

CUSTOM_FILE = 'custom_data.json'

def load_initial_data():
    """Reads the file from disk once."""
    if os.path.exists(CUSTOM_FILE):
        try:
            with open(CUSTOM_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading {CUSTOM_FILE}: {e}")
            return {}
    return {}

# --- CACHE ---
CACHED_DATA = load_initial_data()

def get_text(key, default_text):
    """Returns String (for messages/buttons)"""
    return str(CACHED_DATA.get(key, default_text))

def get_data(key, default_value=None):
    """Returns List or Dict (for admin menu structure)"""
    return CACHED_DATA.get(key, default_value)

def set_text(key, new_value):
    """Updates Memory and File"""
    CACHED_DATA[key] = new_value
    try:
        with open(CUSTOM_FILE, 'w', encoding='utf-8') as f:
            json.dump(CACHED_DATA, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False
