import os

# আপনার বট টোকেন
BOT_TOKEN = "8532051721:AAFYCczECYY2_icKsCZcjVGbxCthQMlOR5c"

# এডমিন হওয়ার পাসওয়ার্ড (/admin_login Password)
ADMIN_PASSWORD = "Admin" 

# ব্যাকআপ এডমিন এবং ওয়াটারমার্ক টুল এডমিন (মাস্ট নিজের আইডি দিন)
SUPER_ADMINS = [7936925985] 

# ব্যাকআপ চ্যানেল আইডি (অপশনাল)
BACKUP_CHANNEL_ID = -1003546352030

# ডাটাবেস ফাইল পাথ
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CUSTOM_FILE = os.path.join(DATA_DIR, "custom_data.json")

# ফোল্ডার নিশ্চিত করা
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


#কোডটি রান করতে যে পক্যাকাজগুলো মাস্ট ডাউনলোড করা লাগবেই
# telebot
#qrcode
#imageio-ffmpeg
#pillow
#numpy
#ffmpeg
#pyTelegramBotAPI
#pyshorteners
#moviepy