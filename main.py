import telebot
import time
import threading
import os
from config import BOT_TOKEN

# --- 1. CORE HANDLERS ---
from handlers.start import register_start
from handlers.auth import register_auth_handlers
from handlers.admin_panel import register_admin_handlers

# --- 2. TOOLS HANDLERS (New Updates) ---
from handlers.tools.url_shorten import register_url_handlers      # ✅ URL Shortener
from handlers.tools.watermark import register_watermark_handlers  # ✅ Watermark
from handlers.tools.group_management import register_commands as register_group_tools 

# --- 3. SHOP & OTHERS HANDLERS (Legacy) ---
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

# টোকেন চেক
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in config.py")

# বট ইনিশিলাইজেশন
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =========================================================
# 📥 REGISTER HANDLERS (Order is Very Important!)
# =========================================================
print("📥 Registering handlers...")

# ১. বেসিক কমান্ড (Start/Admin)
register_start(bot)
register_auth_handlers(bot)
register_admin_handlers(bot)

# ---------------------------------------------------------
# 🔥 CRITICAL SECTION: TOOLS ORDER
# ---------------------------------------------------------

# ২. URL Shortener (সবার আগে)
# কারণ: এটি স্পেসিফিক লিংক চেক করে। এটি নিচে থাকলে Watermark টুল লিংকটিকে সাধারণ টেক্সট মনে করে খেয়ে ফেলবে।
register_url_handlers(bot)

# ৩. Group Management
# গ্রুপ টুলস এবং কমান্ড হ্যান্ডল করার জন্য
register_group_tools(bot)

# ৪. Watermark Tool
# কারণ: এটি মিডিয়া এবং বাকি সাধারণ টেক্সট হ্যান্ডল করে।
register_watermark_handlers(bot)

# ---------------------------------------------------------

# ৫. শপ এবং অন্যান্য ফিচার (Shop Handlers)
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

# ৬. গ্লোবাল কলব্যাক (সবার শেষে)
register_callbacks(bot)

print("✅ All handlers registered successfully.")

# =========================================================
# ⏰ SCHEDULER (Background Task)
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
# 🚀 START BOT
# =========================================================
if __name__ == "__main__":
    # প্রয়োজনীয় ফোল্ডার তৈরি আছে কিনা চেক
    if not os.path.exists("data"): os.makedirs("data")
    if not os.path.exists("data/fonts"): os.makedirs("data/fonts")
    
    print("🤖 Bot is running...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ Critical Error: {e}")
