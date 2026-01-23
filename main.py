import telebot
import time
import threading
import os
import json
import sys

# =========================================================
# ⚙️ 1. CONFIGURATION LOAD
# =========================================================
try:
    # config থেকে সব পাথ এবং টোকেন ইমপোর্ট করা হচ্ছে
    from config import BOT_TOKEN, DATA_DIR, USERS_FILE, SHOPS_FILE, CUSTOM_FILE
except ImportError:
    print("❌ Critical Error: config.py not found!")
    print("Please create secrets.py and config.py first.")
    sys.exit(1)

# টোকেন চেক
if not BOT_TOKEN:
    raise RuntimeError("⚠️ BOT_TOKEN is missing in secrets.py/config.py")

# বট ইনিশিলাইজেশন
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =========================================================
# 🛠 2. SYSTEM CHECK & AUTO-FIX (Startup Logic)
# =========================================================
def check_and_create_files():
    """বট রান করার আগে সব ফোল্ডার এবং জেসন ফাইল চেক করে তৈরি করে"""
    print("🔍 Checking system files...")

    # ১. ডাটা ফোল্ডার চেক
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"✅ Created folder: {DATA_DIR}")
    
    # ফন্টস ফোল্ডার (Watermark এর জন্য)
    fonts_dir = os.path.join(DATA_DIR, "fonts")
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)

    # ২. ইউজার ডাটাবেস (Users DB)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f: json.dump({}, f)
        print("✅ Created users.json")

    # ৩. শপ ডাটাবেস (Shops DB)
    if not os.path.exists(SHOPS_FILE):
        with open(SHOPS_FILE, 'w') as f: json.dump({}, f)
        print("✅ Created shops.json")

    # ৪. কাস্টম ডাটা / সেটিংস (Settings DB)
    if not os.path.exists(CUSTOM_FILE):
        default_settings = {
            "texts": {
                "welcome": "Welcome to the group!",
                "rules": "Respect admins."
            },
            "banwords": [],
            "warns": {},
            "admin_menu_structure": {
                "main_menu": [["🔘 Edit Tools Button", "main_btn_tools"]]
            }
        }
        with open(CUSTOM_FILE, 'w') as f: json.dump(default_settings, f)
        print("✅ Created custom_data.json")

# =========================================================
# 📥 3. HANDLERS IMPORT
# =========================================================
print("📥 Loading handlers...")

try:
    # --- CORE ---
    from handlers.start import register_start
    from handlers.auth import register_auth_handlers
    from handlers.admin_panel import register_admin_handlers

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
    
    # --- UTILS ---
    from utils.utils_shop import get_and_clear_due_posts

except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("Make sure all handler files exist and __init__.py is handled correctly.\n")
    # আমরা এখানে exit করছি না, যাতে লগ দেখে ফিক্স করা যায়, তবে হ্যান্ডলার মিসিং থাকলে বট ঠিকমতো কাজ করবে না
    time.sleep(5) 

# =========================================================
# 📝 4. REGISTER HANDLERS (Execution Order)
# =========================================================
print("🔗 Registering handlers...")

# ১. বেসিক কমান্ড (Start/Admin)
register_start(bot)
register_auth_handlers(bot)
register_admin_handlers(bot)

# ২. টুলস (Tools)
register_url_handlers(bot)       # Regex Filter
register_watermark_handlers(bot) # State Filter
register_group_tools(bot)        # Group Commands

# ৩. শপ এবং বিজনেস (Shop Handlers)
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

# ৪. গ্লোবাল কলব্যাক (Must be last)
register_callbacks(bot)

print("✅ All handlers registered successfully.")

# =========================================================
# ⏰ 5. SCHEDULER (Background Task)
# =========================================================
def scheduler_loop():
    print("⏰ Scheduler started...")
    while True:
        try:
            # ডিউ পোস্ট চেক করা এবং চ্যানেলে পোস্ট করা
            tasks = get_and_clear_due_posts()
            if tasks:
                for t in tasks:
                    post_product_to_channel(
                        bot, 
                        t['channel_id'], 
                        t['product'], 
                        t['shop_name'], 
                        None, 
                        bot.get_me().username
                    )
            time.sleep(60) # প্রতি ১ মিনিটে চেক করবে
        except Exception as e:
            print(f"⚠️ Scheduler Error: {e}")
            time.sleep(60)

# শিডিউলার ব্যাকগ্রাউন্ডে রান করা
threading.Thread(target=scheduler_loop, daemon=True).start()

# =========================================================
# 🚀 6. MAIN LOOP (Start Bot)
# =========================================================
if __name__ == "__main__":
    # ১. ফাইল চেক করা
    check_and_create_files()
    
    print("\n🤖 Bot is running...")
    print("ℹ️  Press Ctrl+C to stop.\n")
    
    # ২. ইনফিনিটি পোলিং (নেটওয়ার্ক এরর হ্যান্ডেল করার জন্য)
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Critical Polling Error: {e}")
            print("🔄 Restarting in 5 seconds...")
            time.sleep(5)
