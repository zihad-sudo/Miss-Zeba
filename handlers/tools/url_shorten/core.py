import requests
import json
import re
import os
import uuid
from io import BytesIO
from telebot import types
from PIL import Image

# Utils থেকে ইম্পোর্ট
from handlers.tools.url_shorten.qr_utils import load_colors, add_new_color, generate_palette_page, make_qr, generate_gradient_palette_page

# -------------------------------
# CONFIGURATION & DATA FILES
# -------------------------------
TEXT_ENDPOINT = "https://spoo.me/"
EMOJI_ENDPOINT = "https://spoo.me/emoji"

GLOBAL_THEMES_FILE = "data/themes_global.json"
USER_THEMES_FILE = "data/themes_user.json"

QR_STYLES = ['square', 'round', 'diamond', 'vertical', 'horizontal', 'rounded', 'star']
# 🔥 গ্রেডিয়েন্ট লিস্ট (None মানে সলিড কালার)
GRADIENT_LIST = [None, 'sunset', 'ocean', 'forest', 'purple_love', 'fire', 'sky', 'royal']

user_state = {}

# -------------------------------
# 1. DATA MANAGEMENT (JSON)
# -------------------------------
def load_json(path, default_val):
    if not os.path.exists(path):
        if not os.path.exists('data'): 
            os.makedirs('data')
        with open(path, 'w') as f: 
            json.dump(default_val, f)
        return default_val
    try:
        with open(path, 'r') as f: 
            return json.load(f)
    except: 
        return default_val

def save_json(path, data):
    with open(path, 'w') as f: json.dump(data, f, indent=4)

def get_global_themes(): return load_json(GLOBAL_THEMES_FILE, [])
def add_global_theme(theme):
    data = get_global_themes(); data.insert(0, theme); save_json(GLOBAL_THEMES_FILE, data)

def get_user_themes(cid): 
    return load_json(USER_THEMES_FILE, {}).get(str(cid), [])

def add_user_theme(cid, theme):
    all_data = load_json(USER_THEMES_FILE, {})
    if str(cid) not in all_data: all_data[str(cid)] = []
    all_data[str(cid)].insert(0, theme)
    save_json(USER_THEMES_FILE, all_data)

def delete_user_theme(cid, theme_id):
    all_data = load_json(USER_THEMES_FILE, {})
    if str(cid) in all_data:
        all_data[str(cid)] = [t for t in all_data[str(cid)] if t['id'] != theme_id]
        save_json(USER_THEMES_FILE, all_data)

# -------------------------------
# 2. STATE & MENU SYSTEM
# -------------------------------
def init_user(cid):
    if cid not in user_state:
        user_state[cid] = {
            'qr': True, 'emoji': False, 'color': 'black', 'style': 'square', 
            'logo': None, 'action': None, 'page': 0, 'gradient': None
        }

def get_dashboard_menu(cid):
    init_user(cid); s = user_state[cid]
    mk = types.InlineKeyboardMarkup(row_width=2)
    
    mk.add(
        types.InlineKeyboardButton(f"Emoji: {'ON' if s['emoji'] else 'OFF'}", callback_data="url_set_emoji"),
        types.InlineKeyboardButton(f"QR Mode: {'ON' if s['qr'] else 'OFF'}", callback_data="url_set_qr")
    )
    
    if s['qr']:
        # ১. কালার বাটন লজিক: গ্রেডিয়েন্ট থাকলে এটি লক দেখাবে এবং ক্লিক করলে আনলক হ্যান্ডলার কল করবে
        if not s['gradient']:
            col_btn = types.InlineKeyboardButton(f"🎨 Color: {s['color'].title()}", callback_data="url_menu_color")
        else:
            col_btn = types.InlineKeyboardButton(f"🎨 Color: Locked 🔒", callback_data="url_unlock_color")

        mk.add(
            col_btn,
            types.InlineKeyboardButton(f"💠 {s['style'].title()}", callback_data="url_tog_style")
        )
        
        # ২. গ্রেডিয়েন্ট বাটন: এখানে বর্তমানে সিলেক্ট করা গ্রেডিয়েন্টের নাম দেখাবে
        grad_display = s['gradient'].title() if s['gradient'] else "None (Solid)"
        mk.add(types.InlineKeyboardButton(f"🌈 Gradient: {grad_display}", callback_data="url_menu_grad"))

        mk.add(types.InlineKeyboardButton(f"🖼️ Logo: {'Set ✅' if s['logo'] else 'None ❌'}", callback_data="url_up_logo"))
        mk.add(types.InlineKeyboardButton("👁️ Preview Design", callback_data="url_preview"))
        
        mk.row(
            types.InlineKeyboardButton("🌐 Browse Themes", callback_data="thm_browse_0"),
            types.InlineKeyboardButton("📂 My Themes", callback_data="thm_mine_0")
        )
    
    mk.add(types.InlineKeyboardButton("🔙 Back to Tools", callback_data="back_to_tools"))
    return mk


def get_color_menu(page):
    colors = load_colors()
    color_keys = list(colors.keys())
    items_per_page = 10
    total_pages = (len(color_keys) + items_per_page - 1) // items_per_page
    start_idx = page * items_per_page; end_idx = start_idx + items_per_page
    current_colors = color_keys[start_idx:end_idx]
    
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(name.title(), callback_data=f"url_col_{name}") for name in current_colors]
    mk.add(*btns)
    
    nav_btns = []
    if page > 0: nav_btns.append(types.InlineKeyboardButton("⬅️ Prev", callback_data="url_page_prev"))
    nav_btns.append(types.InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="ignore"))
    if page < total_pages - 1: nav_btns.append(types.InlineKeyboardButton("Next ➡️", callback_data="url_page_next"))
        
    mk.add(*nav_btns)
    mk.add(types.InlineKeyboardButton("➕ Add Color", callback_data="url_add_color"))
    mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="url_home"))
    return mk
    
def get_gradient_menu(page): # এখানে cid এর বদলে page দিন
    from handlers.tools.url_shorten.qr_utils import load_gradients
    all_grads = load_gradients()
    grad_keys = list(all_grads.keys())
    
    # পেজিনেশন লজিক (কালার মেনুর মতো)
    items_per_page = 10
    total_pages = (len(grad_keys) + items_per_page - 1) // items_per_page
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_grads = grad_keys[start_idx:end_idx]
    
    mk = types.InlineKeyboardMarkup(row_width=2)
    
    # প্রথম পেজে None অপশন রাখা
    if page == 0:
        mk.add(types.InlineKeyboardButton("🚫 None (Solid Color)", callback_data="url_set_grad_None"))
    
    # বাটন তৈরি
    btns = [types.InlineKeyboardButton(g.title(), callback_data=f"url_set_grad_{g}") for g in current_grads]
    mk.add(*btns)
    
    # নেভিগেশন বাটন
    nav_btns = []
    if page > 0: nav_btns.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"url_grad_pg_{page-1}"))
    nav_btns.append(types.InlineKeyboardButton(f"📄 {page + 1}/{max(1, total_pages)}", callback_data="ignore"))
    if page < total_pages - 1: nav_btns.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"url_grad_pg_{page+1}"))
    mk.row(*nav_btns)
    
    mk.add(types.InlineKeyboardButton("➕ Add New Gradient", callback_data="url_add_grad"))
    mk.add(types.InlineKeyboardButton("🔙 Back to Dashboard", callback_data="url_home"))
    return mk



# ... (Theme Menu Functions same as before, omitted for brevity but include in file) ...
def get_theme_list_menu(themes, page, prefix, allow_create=False):
    mk = types.InlineKeyboardMarkup(row_width=1)
    items_per_page = 5
    total_pages = (len(themes) + items_per_page - 1) // items_per_page
    start = page * items_per_page; end = start + items_per_page
    chunk = themes[start:end]
    if allow_create: mk.add(types.InlineKeyboardButton("➕ Save Current as New Theme", callback_data="thm_create_new"))
    for t in chunk: mk.add(types.InlineKeyboardButton(f"🎨 {t['name']} (by {t.get('author', 'Unknown')})", callback_data=f"{prefix}_view_{t['id']}"))
    nav = []
    if page > 0: nav.append(types.InlineKeyboardButton("⬅️", callback_data=f"{prefix}_pg_{page-1}"))
    nav.append(types.InlineKeyboardButton(f"📄 {page+1}/{max(1, total_pages)}", callback_data="ignore"))
    if page < total_pages - 1: nav.append(types.InlineKeyboardButton("➡️", callback_data=f"{prefix}_pg_{page+1}"))
    mk.row(*nav)
    mk.add(types.InlineKeyboardButton("🔙 Back to Dashboard", callback_data="url_home"))
    return mk

def open_url_tool(bot, message, is_edit=False):
    cid = message.chat.id
    init_user(cid)
    text = "🔗 **URL Shortener & QR Studio**\n\nConfigure your style below, then **Send any Link** to process."
    markup = get_dashboard_menu(cid)
    if is_edit:
        try:
            if message.content_type == 'photo':
                bot.delete_message(cid, message.message_id)
                bot.send_message(cid, text, reply_markup=markup, parse_mode="Markdown")
            else:
                bot.edit_message_text(text, cid, message.message_id, reply_markup=markup, parse_mode="Markdown")
        except: bot.send_message(cid, text, reply_markup=markup, parse_mode="Markdown")
    else: bot.send_message(cid, text, reply_markup=markup, parse_mode="Markdown")

# -------------------------------
# 3. CORE LOGIC
# -------------------------------
def process_url(bot, message):
    cid = message.chat.id
    url = message.text.strip()
    init_user(cid); s = user_state[cid]
    msg = bot.reply_to(message, "⏳ **Generating...**", parse_mode="Markdown")

    try:
        target = EMOJI_ENDPOINT if s['emoji'] else TEXT_ENDPOINT
        payload = {'url': url}
        if s['emoji']: payload['emoji'] = "true"
        headers = {"content-type": "application/x-www-form-urlencoded", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
        r = requests.post(target, data=payload, headers=headers, timeout=10)
        
        if r.status_code == 200:
            try: short = r.json().get("short_url")
            except: short = None

            if short:
                disp = url[:100] + "..." if len(url)>100 else url
                text = f"✅ **Link Ready!**\n\n🔗 {disp}\n🚀 `{short}`"

                if s['qr']:
                    # Pass Gradient
                    qr_img = make_qr(short, s['style'], s['color'], s['logo'], gradient_name=s['gradient'])
                    if qr_img:
                        bot.delete_message(cid, msg.message_id)
                        bot.send_photo(cid, qr_img, caption=text, parse_mode="Markdown", reply_markup=get_dashboard_menu(cid))
                    else: bot.edit_message_text(text, cid, msg.message_id, parse_mode="Markdown", reply_markup=get_dashboard_menu(cid))
                else: bot.edit_message_text(text, cid, msg.message_id, parse_mode="Markdown", reply_markup=get_dashboard_menu(cid))
            else:
                err = r.json().get('message', 'API Error'); bot.edit_message_text(f"❌ Failed: {err}", cid, msg.message_id)
        else: bot.edit_message_text(f"❌ Server Error: {r.status_code}", cid, msg.message_id)
    except Exception as e: bot.edit_message_text(f"❌ Error: {str(e)[:50]}", cid, msg.message_id)

# -------------------------------
# 4. HANDLERS REGISTER
# -------------------------------
def register_url_handlers(bot):
    
    def show_color_page(cid, page, message_id=None, is_edit=False):
        img_bio = generate_palette_page(page); markup = get_color_menu(page)
        if img_bio:
            if is_edit and message_id:
                try:
                    media = types.InputMediaPhoto(img_bio, caption="🎨 **Select a Color:**")
                    bot.edit_message_media(media=media, chat_id=cid, message_id=message_id, reply_markup=markup)
                except:
                    try: bot.delete_message(cid, message_id)
                    except: pass
                    bot.send_photo(cid, img_bio, caption="🎨 **Select a Color:**", reply_markup=markup)
            else: bot.send_photo(cid, img_bio, caption="🎨 **Select a Color:**", reply_markup=markup)

    # --- GRADIENT HANDLER ---
    # এটি register_url_handlers(bot): এর ভেতরে পেস্ট করুন (show_color_page এর নিচে)
    
    def show_gradient_page(cid, page, message_id=None, is_edit=False):
        # ১. qr_utils থেকে গ্রেডিয়েন্ট প্যালেটের ছবি জেনারেট করা
        img_bio = generate_gradient_palette_page(page)
        # ২. বাটন মেনু আনা
        markup = get_gradient_menu(page)
        
        caption_text = "🌈 **Select a Gradient Style:**\nNote: Selecting a gradient will override solid colors."

        if img_bio:
            if is_edit and message_id:
                try:
                    # আগের মেসেজটি যদি ফটো হয়, তবে মিডিয়া এডিট করা
                    media = types.InputMediaPhoto(img_bio, caption=caption_text, parse_mode="Markdown")
                    bot.edit_message_media(media=media, chat_id=cid, message_id=message_id, reply_markup=markup)
                except:
                    # যদি আগেরটি টেক্সট হয়, তবে সেটি ডিলিট করে নতুন ফটো পাঠানো
                    try: bot.delete_message(cid, message_id)
                    except: pass
                    bot.send_photo(cid, img_bio, caption=caption_text, reply_markup=markup, parse_mode="Markdown")
            else:
                # নতুন করে ফটো পাঠানো
                bot.send_photo(cid, img_bio, caption=caption_text, reply_markup=markup, parse_mode="Markdown")
        else:
            # যদি কোনো কারণে ইমেজ তৈরি না হয় (যেমন লিস্ট খালি থাকলে)
            bot.send_message(cid, "No gradients found.", reply_markup=markup)

    # --- ১. গ্রেডিয়েন্ট মেনু ওপেন করার হ্যান্ডলার (Visual Update) ---
    @bot.callback_query_handler(func=lambda c: c.data == "url_menu_grad")
    def show_grad_menu(c):
        cid = c.message.chat.id
        # টেক্সট এডিটের বদলে ছবিসহ পেজ ফাংশনটি কল করুন
        show_gradient_page(cid, 0, message_id=c.message.message_id, is_edit=True)

    # --- ২. গ্রেডিয়েন্ট মেনুর পেজিনেশন হ্যান্ডলার (Visual Update) ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("url_grad_pg_"))
    def handle_grad_pagination(c):
        cid = c.message.chat.id
        new_page = int(c.data.split("_")[-1])
        # পেজ পরিবর্তনের সময়ও ছবিসহ আপডেট হবে
        show_gradient_page(cid, new_page, message_id=c.message.message_id, is_edit=True)


    # --- ৩. নতুন গ্রেডিয়েন্ট যোগ করার জন্য ইনপুট চাওয়া ---
    @bot.callback_query_handler(func=lambda c: c.data == "url_add_grad")
    def ask_new_gradient(c):
        cid = c.message.chat.id
        init_user(cid)
        user_state[cid]['action'] = 'waiting_grad_input'
        try: bot.delete_message(cid, c.message.message_id)
        except: pass
        
        msg = "➕ **Add New Gradient:**\n\n"
        msg += "নিচের ফরম্যাটে মেসেজ পাঠান:\n`নাম #Hex1 #Hex2`\n\n"
        msg += "উদাহরণ:\n`Sunset #FF512F #DD2476` \n\n"
        msg += "(একাধিক যোগ করতে প্রতি লাইনে একটি করে দিন)"
        bot.send_message(cid, msg, parse_mode="Markdown")

    # --- ৪. ইউজারের পাঠানো গ্রেডিয়েন্ট প্রসেস ও সেভ করা ---
    @bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get('action') == 'waiting_grad_input')
    def process_new_gradient_input(m):
        cid = m.chat.id
        text = m.text.strip()
        added = []
        
        # প্রতি লাইন আলাদা করে চেক করা
        for line in text.split('\n'):
            line = line.strip()
            if not line: continue
            
            # Regex: নাম তারপর দুটি Hex কালার কোড
            match = re.search(r'^([a-zA-Z0-9_ ]+?)\s+(#?[0-9a-fA-F]{6})\s+(#?[0-9a-fA-F]{6})$', line)
            if match:
                name = match.group(1).strip()
                h1, h2 = match.group(2), match.group(3)
                
                # qr_utils থেকে ফাংশন ইম্পোর্ট করে সেভ করা
                from handlers.tools.url_shorten.qr_utils import add_new_gradient
                add_new_gradient(name, h1, h2)
                added.append(name.title())
        
        # অ্যাকশন ক্লিয়ার করা
        user_state[cid]['action'] = None
        
        if added:
            success_msg = f"✅ সফলভাবে যোগ করা হয়েছে:\n" + ", ".join(added)
            bot.reply_to(m, success_msg, reply_markup=get_dashboard_menu(cid))
        else:
            bot.reply_to(m, "❌ ফরম্যাট ভুল ছিল! \nসঠিক ফরম্যাট: `নাম #Hex1 #Hex2`", reply_markup=get_dashboard_menu(cid))

    # --- ৫. গ্রেডিয়েন্ট সিলেক্ট বা সেট করার হ্যান্ডলার ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("url_set_grad_"))
    def set_gradient_choice(c):
        cid = c.message.chat.id
        init_user(cid)
        grad_val = c.data.replace("url_set_grad_", "")
        
        if grad_val == "None":
            user_state[cid]['gradient'] = None
            bot.answer_callback_query(c.id, "✅ Solid Color Mode Active")
        else:
            user_state[cid]['gradient'] = grad_val
            bot.answer_callback_query(c.id, f"✅ Gradient: {grad_val.title()} set!")
        
        # ড্যাশবোর্ড আপডেট করা
        open_url_tool(bot, c.message, is_edit=True)


        # এই হ্যান্ডলারটি যোগ করুন
        # register_url_handlers(bot): এর ভেতর এই অংশটি পেস্ট করুন
    @bot.callback_query_handler(func=lambda c: c.data == "url_unlock_color")
    def unlock_color_action(c):
        cid = c.message.chat.id
        init_user(cid)
        user_state[cid]['gradient'] = None
        bot.answer_callback_query(c.id, "🔓 Gradient disabled! Solid colors unlocked.", show_alert=False)
        user_state[cid]['page'] = 0
        show_color_page(cid, 0, message_id=c.message.message_id, is_edit=True)


    # --- MARKETPLACE & OTHER HANDLERS ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("thm_browse_"))
    def browse_global(c):
        page = int(c.data.split("_")[-1]) if "browse" in c.data else 0
        themes = get_global_themes()
        mk = get_theme_list_menu(themes, page, "gthm", allow_create=False)
        try:
            if c.message.content_type == 'photo':
                bot.delete_message(c.message.chat.id, c.message.message_id)
                bot.send_message(c.message.chat.id, "🌐 **Global Theme Gallery:**", reply_markup=mk, parse_mode="Markdown")
            else: bot.edit_message_text("🌐 **Global Theme Gallery:**", c.message.chat.id, c.message.message_id, reply_markup=mk, parse_mode="Markdown")
        except: bot.send_message(c.message.chat.id, "🌐 **Global Theme Gallery:**", reply_markup=mk, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("thm_mine_"))
    def browse_mine(c):
        cid = c.message.chat.id; page = int(c.data.split("_")[-1]) if "mine" in c.data else 0
        themes = get_user_themes(cid)
        mk = get_theme_list_menu(themes, page, "mthm", allow_create=True)
        text = "📂 **My Saved Themes:**\nSelect a theme to Apply or Publish."
        try:
            if c.message.content_type == 'photo':
                bot.delete_message(cid, c.message.message_id)
                bot.send_message(cid, text, reply_markup=mk, parse_mode="Markdown")
            else: bot.edit_message_text(text, cid, c.message.message_id, reply_markup=mk, parse_mode="Markdown")
        except: bot.send_message(cid, text, reply_markup=mk, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: "_view_" in c.data)
    def view_theme(c):
        cid = c.message.chat.id; theme_id = c.data.split("_")[-1]; is_global = c.data.startswith("gthm")
        source = get_global_themes() if is_global else get_user_themes(cid)
        theme = next((t for t in source if t['id'] == theme_id), None)
        if not theme: bot.answer_callback_query(c.id, "❌ Theme not found."); return

        s = theme['settings']
        # Preview with Gradient
        qr_img = make_qr("https://t.me/MissZeba_bot", s['style'], s['color'], None, gradient_name=s.get('gradient'))
        
        if qr_img:
            mk = types.InlineKeyboardMarkup()
            if is_global:
                mk.add(types.InlineKeyboardButton("⬇️ Add to My Themes", callback_data=f"thm_save_{theme_id}"))
                mk.add(types.InlineKeyboardButton("🔙 Back to Gallery", callback_data="thm_browse_0"))
            else:
                mk.add(types.InlineKeyboardButton("✅ Apply Theme", callback_data=f"thm_apply_{theme_id}"))
                mk.row(types.InlineKeyboardButton("🌍 Publish", callback_data=f"thm_pub_{theme_id}"), types.InlineKeyboardButton("🗑️ Delete", callback_data=f"thm_del_{theme_id}"))
                mk.add(types.InlineKeyboardButton("🔙 Back to My Themes", callback_data="thm_mine_0"))
            
            caption = f"🎨 **Theme:** {theme['name']}\n👤 **Author:** {theme.get('author','Unknown')}\n\nStyle: `{s['style']}` | Color: `{s['color']}` | Grad: `{s.get('gradient', 'None')}`"
            try: bot.delete_message(cid, c.message.message_id)
            except: pass
            bot.send_photo(cid, qr_img, caption=caption, reply_markup=mk, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("thm_save_"))
    def save_theme_to_mine(c):
        cid = c.message.chat.id; theme_id = c.data.split("_")[-1]
        theme = next((t for t in get_global_themes() if t['id'] == theme_id), None)
        if theme:
            new_theme = theme.copy(); new_theme['id'] = str(uuid.uuid4())[:8]
            add_user_theme(cid, new_theme); bot.answer_callback_query(c.id, "✅ Saved!", show_alert=True)
        else: bot.answer_callback_query(c.id, "❌ Error.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("thm_apply_"))
    def apply_theme(c):
        cid = c.message.chat.id; theme_id = c.data.split("_")[-1]
        theme = next((t for t in get_user_themes(cid) if t['id'] == theme_id), None)
        if theme:
            s = theme['settings']; init_user(cid)
            user_state[cid].update({'color': s['color'], 'style': s['style'], 'gradient': s.get('gradient')})
            bot.answer_callback_query(c.id, "✅ Applied!"); open_url_tool(bot, c.message, is_edit=False)
        else: bot.answer_callback_query(c.id, "❌ Error.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("thm_del_"))
    def delete_theme_action(c):
        cid = c.message.chat.id; theme_id = c.data.split("_")[-1]
        delete_user_theme(cid, theme_id); bot.answer_callback_query(c.id, "🗑️ Deleted."); browse_mine(c)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("thm_pub_"))
    def publish_theme_action(c):
        cid = c.message.chat.id; theme_id = c.data.split("_")[-1]
        theme = next((t for t in get_user_themes(cid) if t['id'] == theme_id), None)
        if theme:
            pub_theme = theme.copy(); pub_theme['author'] = c.from_user.first_name
            add_global_theme(pub_theme); bot.answer_callback_query(c.id, "🌍 Published!", show_alert=True)
        else: bot.answer_callback_query(c.id, "❌ Error.")

    @bot.callback_query_handler(func=lambda c: c.data == "thm_create_new")
    def create_new_theme(c):
        cid = c.message.chat.id; init_user(cid); user_state[cid]['action'] = 'waiting_theme_name'
        try: bot.delete_message(cid, c.message.message_id)
        except: pass
        bot.send_message(cid, "📝 **Enter a Name for your Theme:**", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get('action') == 'waiting_theme_name')
    def save_theme_name(m):
        cid = m.chat.id; name = m.text.strip()
        if len(name) > 20: name = name[:20]
        s = user_state[cid]
        new_theme = {
            "id": str(uuid.uuid4())[:8], "name": name, "author": m.from_user.first_name,
            "settings": {"color": s['color'], "style": s['style'], "gradient": s.get('gradient')}
        }
        add_user_theme(cid, new_theme); user_state[cid]['action'] = None
        bot.reply_to(m, f"✅ Theme **{name}** saved!", reply_markup=get_dashboard_menu(cid))

    @bot.callback_query_handler(func=lambda c: c.data == "url_preview")
    def show_preview(c):
        cid = c.message.chat.id; init_user(cid); s = user_state[cid]
        qr_img = make_qr("https://t.me/MissZeba_bot", s['style'], s['color'], s['logo'], gradient_name=s['gradient'])
        if qr_img:
            try: bot.delete_message(cid, c.message.message_id)
            except: pass
            back_mk = types.InlineKeyboardMarkup(); back_mk.add(types.InlineKeyboardButton("🔙 Back to Editor", callback_data="url_home"))
            caption = f"👁️ **Preview**\n🎨 Color: `{s['color']}`\n💠 Style: `{s['style']}`\n🌈 Grad: `{s['gradient']}`"
            bot.send_photo(cid, qr_img, caption=caption, reply_markup=back_mk, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: c.data == "url_home")
    def go_home(c): open_url_tool(bot, c.message, is_edit=True)

    @bot.callback_query_handler(func=lambda c: c.data in ["url_set_emoji", "url_set_qr", "url_tog_style"])
    def toggles(c):
        cid = c.message.chat.id; init_user(cid)
        if c.data == "url_set_emoji": user_state[cid]['emoji'] = not user_state[cid]['emoji']
        elif c.data == "url_set_qr": user_state[cid]['qr'] = not user_state[cid]['qr']
        elif c.data == "url_tog_style": 
            try: user_state[cid]['style'] = QR_STYLES[(QR_STYLES.index(user_state[cid]['style'])+1)%len(QR_STYLES)]
            except: user_state[cid]['style'] = 'square'
        bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=get_dashboard_menu(cid))

    @bot.callback_query_handler(func=lambda c: c.data == "url_menu_color")
    def col_menu_start(c):
        cid = c.message.chat.id; init_user(cid); user_state[cid]['page'] = 0
        show_color_page(cid, 0, message_id=c.message.message_id, is_edit=True)

    @bot.callback_query_handler(func=lambda c: c.data in ["url_page_prev", "url_page_next"])
    def handle_pagination(c):
        cid = c.message.chat.id; init_user(cid); colors = load_colors(); total_pages = (len(colors)+9)//10
        current = user_state[cid].get('page', 0)
        new_page = max(0, current-1) if c.data=="url_page_prev" else min(total_pages-1, current+1)
        if new_page != current: user_state[cid]['page'] = new_page; show_color_page(cid, new_page, message_id=c.message.message_id, is_edit=True)
        else: bot.answer_callback_query(c.id, "End of list.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("url_col_"))
    def set_col(c):
        cid = c.message.chat.id; init_user(cid); col = c.data.split("_")[-1]
        user_state[cid]['color'] = col
        try: bot.delete_message(cid, c.message.message_id)
        except: pass
        bot.send_message(cid, f"✅ Color set to **{col.title()}**", reply_markup=get_dashboard_menu(cid), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: c.data == "url_add_color")
    def ask_new_color(c):
        cid = c.message.chat.id; init_user(cid); user_state[cid]['action'] = 'waiting_color_input'
        try: bot.delete_message(cid, c.message.message_id)
        except: pass
        bot.send_message(cid, "➕ **Add Colors:**\n`Name Hex`\nEx: `Lime #00FF00`", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get('action') == 'waiting_color_input')
    def save_new_color(m):
        cid = m.chat.id; text = m.text.strip(); added = []
        for line in text.split('\n'):
            line = line.strip(); 
            if not line: continue
            match = re.search(r'^([a-zA-Z0-9_ ]+?)\s+(#?[0-9a-fA-F]{6})$', line)
            if match: add_new_color(match.group(1), match.group(2)); added.append(match.group(1))
        user_state[cid]['action'] = None
        bot.reply_to(m, f"✅ Added {len(added)} colors!", reply_markup=get_dashboard_menu(cid))

    @bot.callback_query_handler(func=lambda c: c.data == "url_up_logo")
    def logo_h(c):
        cid = c.message.chat.id; init_user(cid)
        if user_state[cid]['logo']: user_state[cid]['logo'] = None; bot.answer_callback_query(c.id, "Removed"); bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=get_dashboard_menu(cid))
        else: user_state[cid]['action'] = 'waiting_logo'; bot.send_message(cid, "🖼️ **Send Logo now.**")

    @bot.message_handler(content_types=['photo'], func=lambda m: user_state.get(m.chat.id, {}).get('action') == 'waiting_logo')
    def get_logo(m):
        try:
            data = bot.download_file(bot.get_file(m.photo[-1].file_id).file_path)
            user_state[m.chat.id]['logo'] = data; user_state[m.chat.id]['action'] = None
            bot.reply_to(m, "✅ Logo Set!", reply_markup=get_dashboard_menu(m.chat.id))
        except: pass

    @bot.message_handler(regexp=r"^https?://", func=lambda m: m.chat.type == "private")
    def handle_link_private(m): process_url(bot, m)
