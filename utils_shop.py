import json
import os
import time # <--- Added time for unique IDs

SHOPS_FILE = 'shops.json'

def load_shops():
    if os.path.exists(SHOPS_FILE):
        try:
            with open(SHOPS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_shops(data):
    try:
        with open(SHOPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Shop Save Error: {e}")
        return False

def get_shop(user_id):
    data = load_shops()
    return data.get(str(user_id))

def create_shop(user_id, name):
    data = load_shops()
    uid = str(user_id)
    if uid in data: return False
    
    data[uid] = {
        "owner_id": user_id,
        "name": name,
        "description": "Welcome to my store!",
        "products": {}
    }
    return save_shops(data)

# --- NEW FUNCTION ---
def add_product_to_shop(user_id, name, price, photo_id):
    data = load_shops()
    uid = str(user_id)
    
    if uid not in data: return False
    
    # Generate Unique ID using timestamp
    prod_id = f"prod_{int(time.time())}"
    
    data[uid]["products"][prod_id] = {
        "name": name,
        "price": price,
        "image": photo_id
    }
    return save_shops(data)

# --- NEW FUNCTION ---
def update_shop_desc(user_id, new_desc):
    data = load_shops()
    uid = str(user_id)
    if uid in data:
        data[uid]["description"] = new_desc
        return save_shops(data)
    return False
