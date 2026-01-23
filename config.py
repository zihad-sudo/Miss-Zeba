import os
import sys

# ==========================================
# ⚙️ MAIN CONFIGURATION
# ==========================================

# 1. secrets.py থেকে গোপন তথ্য আনা হচ্ছে
try:
    from secrets import BOT_TOKEN, ADMIN_PASSWORD, SUPER_ADMINS, GITHUB_TOKEN, REPO_NAME
except ImportError:
    print("\n❌ CRITICAL ERROR: 'secrets.py' file not found!")
    print("Please create 'secrets.py' and add BOT_TOKEN, SUPER_ADMINS, etc.")
    sys.exit(1)

# 2. অন্যান্য কনফিগারেশন
BACKUP_CHANNEL_ID = -1003546352030
DEFAULT_TIMEOUT = 60

# 3. ডাটাবেস এবং ফোল্ডার পাথ
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CUSTOM_FILE = os.path.join(DATA_DIR, "custom_data.json")
SHOPS_FILE = os.path.join(DATA_DIR, "shops.json")  # এটিও যুক্ত করে দিলাম যাতে সব পাথ এক জায়গায় থাকে

# 4. ফোল্ডার নিশ্চিত করা (যদি না থাকে তৈরি করবে)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"✅ Created directory: {DATA_DIR}")

print("✅ Configuration loaded successfully.")
