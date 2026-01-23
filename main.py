import telebot
import time
import threading
import os
import json
import sys
import importlib.util # ডায়নামিক লোডিং লাইব্রেরি

# =========================================================
# ⚙️ 1. CONFIGURATION LOAD
# =========================================================
try:
    from config import BOT_TOKEN, DATA_DIR, USERS_FILE, SHOPS_FILE, CUSTOM_FILE
except ImportError:
    print("❌ Critical Error: config.py not found!")
    sys.exit(1)

if not BOT_TOKEN:
    raise RuntimeError("⚠️ BOT_TOKEN is missing")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =========================================================
# 🛠 2. SYSTEM CHECK & AUTO-FIX (Startup Logic)
# =========================================================
def check_and_create_files():
    """বট রান করার আগে সব ফোল্ডার এবং ফাইল নিশ্চিত করে"""
    print("🔍 Checking system files...")

    # মেইন ডাটা ফোল্ডার
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # প্লাগিন ফোল্ডার (যেখানে আপনি নতুন ফোল্ডার তৈরি করবেন)
    plugin_dir = "handlers/plugins"
    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)

    # ফন্টস ফোল্ডার
    fonts_dir = os.path.join(DATA_DIR, "fonts")
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)

    # ডাটাবেস ফাইলসমূহ
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f: json.dump({}, f)

    if not os.path.exists(SHOPS_FILE):
        with open(SHOPS_FILE, 'w') as f: json.dump({}, f)

    if not os.path.exists(CUSTOM_FILE):
        default_settings = {
            "texts": {"welcome": "Welcome!", "rules": "Respect everyone."},
            "banwords": [],
            "warns": {},
            "admin_menu_structure": {"main_menu": [["🔘 Edit Tools Button", "main_btn_tools"]]}
        }
        with open(CUSTOM_FILE, 'w') as f: json.dump(default_settings, f)

    print("✅ System check passed.")

# =========================================================
# 🔌 3. DYNAMIC PLUGIN LOADER (Folder Based)
# =========================================================
def load_plugins(bot):
    """
    handlers/plugins/{folder_name}/{filename}.py থেকে লোড করে
    """
    plugin_base = "handlers/plugins"
    print(f"🔌 Scanning plugins in {plugin_base}...")
    
    count = 0
    if not os.path.exists(plugin_base): return

    # প্রতিটি সাব-ফোল্ডার স্ক্যান করা
    for folder in os.listdir(plugin_base):
        folder_path = os.path.join(plugin_base, folder)
        
        # যদি এটি ফোল্ডার হয়
        if os.path.isdir(folder_path):
            # ফোল্ডারের ভেতর সব .py ফাইল খোঁজা
            for filename in os.listdir(folder_path):
                if filename.endswith(".py") and filename != "__init__.py":
                    module_name = f"handlers.plugins.{folder}.{filename[:-3]}"
                    file_path = os.path.join(folder_path, filename)
                    
                    try:
                        # ডায়নামিক ইমপোর্ট লজিক
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        
                        # যদি হ্যান্ডলার রেজিস্টার ফাংশন থাকে, তবে রান করা
                        if hasattr(module, "register_handlers"):
                            module.register_handlers(bot)
                            print(f"   ✅ Loaded: {folder} -> {filename}")
                            count += 1
                        else:
                            print(f"   ⚠️ Skipped: {filename} (No register_handlers)")
                            
                    except Exception as e:
                        print(f"   ❌ FAILED to load {filename}: {e}")
                        # ক্র্যাশ এড়াতে খারাপ ফাইল রিনেম করা (Optional)
                        # os.rename(file_path, file_path + ".broken")

    print(f"🔌 Total Dynamic Plugins Loaded: {count}")

# =========================================================
# 📥 4. HANDLERS IMPORT & REGISTRATION
# =========================================================
print("📥 Loading handlers...")

try:
    # --- CORE ---
    from handlers.start import register_start
    from handlers.auth import register_auth_handlers
    from handlers.admin_panel import register_admin_handlers
    
    # --- PLUGIN MANAGER (For Creating Tools) ---
    from handlers.plugin_manager import register_plugin_handler

    # --- TOOLS ---
    from handlers.tools.url_shorten.core import register_url_handlers
    from handlers.tools.watermark.core import register_watermark_handlers
    from handlers.tools.group_management.commands import register_commands as register_group_tools 

    # --- SHOP & OTHERS ---
    from handlers.broadcast import register_broadcast_handlers
    from handlers.shop_seller import register_seller_handlers
    from handlers.shop_buyer import register_buyer_handlers
    from handlers.shop_categories import register_category_handlers
    from handlers.shop_requests import register_request_handlers 
    from handlers.shop_social import register_social_handlers, post_product_to_channel
    from handlers.shop_coupons import register_coupon_handlers
    from handlers.shop_orders import register_order_handlers
    from handlers.shop_analytics import register_analytics_handlers
    from handlers.shop_cart import register_cart_handlers 
    from handlers.callbacks import register_callbacks
    
    from utils.utils_shop import get_and_clear_due_posts

except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("Ensure all files exist in correct folders.\n")
    sys.exit(1)

# --- Registering (Order Matters) ---
print("🔗 Registering handlers...")

# ১. কোর
register_start(bot)
register_auth_handlers(bot)
register_admin_handlers(bot)
register_plugin_handler(bot) # ✅ প্লাগিন আপলোড লিসেনার

# ২. টুলস
register_url_handlers(bot)
register_watermark_handlers(bot)
register_group_tools(bot)

# ৩. শপ
register_broadcast_handlers(bot)
register_seller_handlers(bot)
register_buyer_handlers(bot)
register_category_handlers(bot)
register_request_handlers(bot)
register_social_handlers(bot)
register_coupon_handlers(bot)
register_order_handlers(bot)
register_analytics_handlers(bot)
register_cart_handlers(bot)

# ৪. ডায়নামিক প্লাগিন লোড
load_plugins(bot)

# ৫. কলব্যাক (সবার শেষে)
register_callbacks(bot)

print("✅ All handlers registered.")

# =========================================================
# ⏰ 5. SCHEDULER & MAIN LOOP
# =========================================================
def scheduler_loop():
    print("⏰ Scheduler started...")
    while True:
        try:
            tasks = get_and_clear_due_posts()
            if tasks:
                for t in tasks:
                    post_product_to_channel(bot, t['channel_id'], t['product'], t['shop_name'], None, bot.get_me().username)
            time.sleep(60)
        except Exception: time.sleep(60)

threading.Thread(target=scheduler_loop, daemon=True).start()

if __name__ == "__main__":
    check_and_create_files()
    
    print("\n🤖 Bot is running with Advanced Plugin System...")
    print("ℹ️  Press Ctrl+C to stop.\n")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Polling Error: {e}")
            print("🔄 Restarting in 5s...")
            time.sleep(5)
