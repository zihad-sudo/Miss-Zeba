import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# File Constants
DEFAULTS_FILE = 'defaults.json'
CUSTOM_FILE = 'custom_data.json'

def load_json_file(filename):
    """Safe file loader that returns an empty dict if file is missing/broken."""
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print(f"⚠️ Warning: Could not read {filename}")
        return {}

def get_tools_layout():
    """
    Loads defaults, checks for custom overrides, and builds the layout.
    """
    # 1. Load the Base Data
    final_data = load_json_file(DEFAULTS_FILE)
    
    # 2. Load the Custom Data
    custom_data = load_json_file(CUSTOM_FILE)
    
    # 3. Update Base with Custom (Only existing keys in custom will overwrite)
    if custom_data:
        final_data.update(custom_data)

    # 4. Extract content (Safe fallback if even defaults are broken)
    text_content = final_data.get("tools_message", "⚠️ Menu Error: Content missing.")
    buttons_list = final_data.get("tools_buttons", [])

    # 5. Build Keyboard
    kb = InlineKeyboardMarkup(row_width=2)
    telebot_buttons = []
    
    for btn in buttons_list:
        telebot_buttons.append(
            InlineKeyboardButton(text=btn['text'], callback_data=btn['callback_data'])
        )
    
    kb.add(*telebot_buttons)
    
    # Add a Back button (Optional but recommended for sub-menus)
    kb.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu_return"))

    return text_content, kb

# --- Main Menu (Unchanged) ---
def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🛠 Tools", callback_data="tools"),
        InlineKeyboardButton("🛒 Shop", callback_data="shop"),
        InlineKeyboardButton("👮 Admin", callback_data="admin"),
        InlineKeyboardButton("📢 Manager", callback_data="manager"),
    )
    return kb
