import json
import os
import time

SHOPS_FILE = 'shops.json'

def load_shops():
    if os.path.exists(SHOPS_FILE):
        try:
            with open(SHOPS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_shops(data):
    try:
        with open(SHOPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error Saving: {e}")
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
        "banner": None,
        "privacy": "public",
        "approved_users": [],
        "pending_requests": [],
        "customers": {},
        "categories": {}, 
        "products": {}
    }
    return save_shops(data)

# --- CATEGORY FUNCTIONS (FIXED) ---
def create_category(user_id, name):
    data = load_shops()
    uid = str(user_id)
    if uid not in data: return False
    
    # ✅ FIX: Auto-Create missing 'categories' dict
    if "categories" not in data[uid]:
        data[uid]["categories"] = {}
        
    cat_id = f"cat_{int(time.time())}"
    data[uid]["categories"][cat_id] = name
    return save_shops(data)

def delete_category(user_id, cat_id):
    data = load_shops()
    uid = str(user_id)
    
    # Check existence safely
    if uid in data and "categories" in data[uid] and cat_id in data[uid]["categories"]:
        del data[uid]["categories"][cat_id]
        
        # Unlink from products
        if "products" in data[uid]:
            for pid in data[uid]["products"]:
                if data[uid]["products"][pid].get("category") == cat_id:
                    data[uid]["products"][pid]["category"] = None
        return save_shops(data)
    return False

def get_categories(user_id):
    data = load_shops()
    uid = str(user_id)
    # Safe retrieval using .get()
    return data.get(uid, {}).get("categories", {})

# --- PRODUCT & OTHER FUNCTIONS ---
def add_product_to_shop(user_id, name, price, description, media_list, category_id=None):
    data = load_shops()
    uid = str(user_id)
    if uid not in data: return False
    
    if "products" not in data[uid]: data[uid]["products"] = {}
        
    prod_id = f"prod_{int(time.time())}"
    data[uid]["products"][prod_id] = {
        "name": name, "price": price, "description": description,
        "media": media_list, "category": category_id, "status": "active", "use_thumbnail": True
    }
    return save_shops(data)

def update_product_field(user_id, prod_id, field, value):
    data = load_shops()
    uid = str(user_id)
    if uid in data and "products" in data[uid] and prod_id in data[uid]["products"]:
        data[uid]["products"][prod_id][field] = value
        return save_shops(data)
    return False

def toggle_product_thumbnail(user_id, prod_id):
    data = load_shops()
    uid = str(user_id)
    if uid in data and "products" in data[uid] and prod_id in data[uid]["products"]:
        current = data[uid]["products"][prod_id].get("use_thumbnail", True)
        data[uid]["products"][prod_id]["use_thumbnail"] = not current
        return save_shops(data)
    return False

def update_shop_desc(user_id, new_desc):
    data = load_shops()
    uid = str(user_id)
    if uid in data:
        data[uid]["description"] = new_desc
        return save_shops(data)
    return False

def set_shop_banner(user_id, photo_id):
    data = load_shops()
    uid = str(user_id)
    if uid in data:
        data[uid]["banner"] = photo_id
        return save_shops(data)
    return False

def delete_product(user_id, prod_id):
    data = load_shops()
    uid = str(user_id)
    if uid in data and "products" in data[uid] and prod_id in data[uid]["products"]:
        del data[uid]["products"][prod_id]
        return save_shops(data)
    return False

def toggle_product_status(user_id, prod_id):
    data = load_shops()
    uid = str(user_id)
    if uid in data and "products" in data[uid] and prod_id in data[uid]["products"]:
        current = data[uid]["products"][prod_id].get("status", "active")
        new_status = "sold" if current == "active" else "active"
        data[uid]["products"][prod_id]["status"] = new_status
        return save_shops(data)
    return False

def toggle_shop_privacy(user_id):
    data = load_shops()
    uid = str(user_id)
    if uid in data:
        current = data[uid].get("privacy", "public")
        data[uid]["privacy"] = "private" if current == "public" else "public"
        return save_shops(data)
    return False

def add_access_request(shop_owner_id, buyer_id, buyer_info):
    data = load_shops()
    soid = str(shop_owner_id)
    if soid in data:
        if "pending_requests" not in data[soid]: data[soid]["pending_requests"] = []
        if "customers" not in data[soid]: data[soid]["customers"] = {}
        if buyer_id not in data[soid]["pending_requests"] and buyer_id not in data[soid].get("approved_users", []):
            data[soid]["pending_requests"].append(buyer_id)
            data[soid]["customers"][str(buyer_id)] = buyer_info 
            save_shops(data)
            return True
    return False

def approve_access(shop_owner_id, buyer_id):
    data = load_shops()
    soid = str(shop_owner_id)
    if soid in data:
        if "approved_users" not in data[soid]: data[soid]["approved_users"] = []
        if "pending_requests" not in data[soid]: data[soid]["pending_requests"] = []
        if buyer_id in data[soid]["pending_requests"]: data[soid]["pending_requests"].remove(buyer_id)
        if buyer_id not in data[soid]["approved_users"]: data[soid]["approved_users"].append(buyer_id)
        return save_shops(data)
    return False

def deny_access(shop_owner_id, buyer_id):
    data = load_shops()
    soid = str(shop_owner_id)
    if soid in data and "pending_requests" in data[soid]:
        if buyer_id in data[soid]["pending_requests"]:
            data[soid]["pending_requests"].remove(buyer_id)
            return save_shops(data)
    return False

def manual_add_buyer(shop_owner_id, target_id, name="Manual Add"):
    data = load_shops()
    soid = str(shop_owner_id)
    if soid in data:
        if "approved_users" not in data[soid]: data[soid]["approved_users"] = []
        if target_id not in data[soid]["approved_users"]:
            data[soid]["approved_users"].append(target_id)
            if "customers" not in data[soid]: data[soid]["customers"] = {}
            data[soid]["customers"][str(target_id)] = {'first_name': name, 'username': 'Unknown'}
            return save_shops(data)
    return False
