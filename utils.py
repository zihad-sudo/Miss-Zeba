# utils.py
import json
import os
from config import SUPER_ADMINS, BACKUP_CHANNEL_ID

CUSTOM_FILE = 'custom_data.json'

def load_initial_data():
    if os.path.exists(CUSTOM_FILE):
        try:
            with open(CUSTOM_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading {CUSTOM_FILE}: {e}")
            return {}
    return {}

CACHED_DATA = load_initial_data()

def send_backup(bot):
    if not bot: return
    try:
        with open(CUSTOM_FILE, 'rb') as f:
            bot.send_document(
                BACKUP_CHANNEL_ID, 
                f, 
                caption="🔄 <b>System Update</b>\nData has been modified.",
                visible_file_name="custom_data.json"
            )
    except Exception as e:
        print(f"⚠️ Backup Failed: {e}")

def reload_data():
    global CACHED_DATA
    CACHED_DATA = load_initial_data()
    return True

def get_text(key, default_text):
    return str(CACHED_DATA.get(key, default_text))

def get_data(key, default_value=None):
    return CACHED_DATA.get(key, default_value)

def is_admin(user_id):
    dynamic_admins = CACHED_DATA.get("admin_ids", [])
    if user_id in dynamic_admins: return True
    if user_id in SUPER_ADMINS: return True
    return False

def set_text(key, new_value, bot=None):
    CACHED_DATA[key] = new_value
    try:
        with open(CUSTOM_FILE, 'w', encoding='utf-8') as f:
            json.dump(CACHED_DATA, f, indent=4, ensure_ascii=False)
        if bot: send_backup(bot)
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

def add_admin(user_id, bot=None):
    current_admins = CACHED_DATA.get("admin_ids", [])
    if user_id not in current_admins:
        current_admins.append(user_id)
        CACHED_DATA["admin_ids"] = current_admins
        try:
            with open(CUSTOM_FILE, 'w', encoding='utf-8') as f:
                json.dump(CACHED_DATA, f, indent=4, ensure_ascii=False)
            if bot: send_backup(bot)
            return True
        except Exception as e:
            return False
    return True
