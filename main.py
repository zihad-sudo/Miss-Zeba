# Main.py

import telebot
import time
import threading
import os
from config import BOT_TOKEN

# =========================================================
# 📥 ১. CORE HANDLERS IMPORT
# =========================================================
from handlers.start import register_start
from handlers.auth import register_auth_handlers
from handlers.admin_panel import register_admin_handlers

# =========================================================
# 🔥 ২. TOOLS HANDLERS (New Filtered Updates)
# =========================================================
from handlers.tools.url_shorten.core import register_url_handlers      # ✅ URL Shortener
from handlers.tools.watermark.core import register_watermark_handlers  # ✅ Watermark
from handlers.tools.group_management import register_commands as register_group_tools 

# =========================================================
# 🛍️ ৩. SHOP & OTHERS HANDLERS (Legacy)
# =========================================================
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

# ---------------------------------------------------------
# 🛡️ BOT INITIALIZATION
# ---------------------------------------------------------
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in config.py")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =========================================================
# 📥 REGISTER HANDLERS (The Strategic Order)
# =========================================================
print("📥 Registering handlers...")

# ১. বেসিক কমান্ড (Start/Admin) - এগুলো সবার আগে থাকবে
register_start(bot)
register_auth_handlers(bot)
register_admin_handlers(bot)

# ২. URL Shortener
# যেহেতু এটি Regex ফিল্টার ব্যবহার করে, একে আগে রাখা নিরাপদ।
register_url_handlers(bot)

# ৩. Watermark Tool
# এটি এখন URL টুলের স্টেট চেক করে কাজ করে, তাই সংঘর্ষ হবে না।
register_watermark_handlers(bot)

# ৪. Group Management
register_group_tools(bot)

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

# ৬. গ্লোবাল কলব্যাক (সবার শেষে Catch-all হিসেবে)
register_callbacks(bot)

print("✅ All handlers registered successfully with Collision Fix.")

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
    
    # এরর হ্যান্ডলিং সহ বট পোলিং
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Critical Polling Error: {e}")
            time.sleep(15) # ১৫ সেকেন্ড অপেক্ষা করে আবার চেষ্টা করবে
