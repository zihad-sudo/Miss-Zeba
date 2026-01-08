import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from utils_shop import get_shop, add_access_request, get_product_rating

buyer_sessions = {}
ITEMS_PER_PAGE = 6

def get_session(user_id):
    if user_id not in buyer_sessions:
        buyer_sessions[user_id] = {'page': 0, 'cat': None, 'sort': 'new', 'search': None}
    return buyer_sessions[user_id]

def register_buyer_handlers(bot):

    @bot.callback_query_handler(func=lambda c: c.data.startswith("view_prods_"))
    def list_shop_content(call):
        shop_id = call.data.replace("view_prods_", "")
        shop = get_shop(shop_id)
        if not shop: 
            bot.answer_callback_query(call.id, "❌ Shop not found.")
            return
        user_id = call.from_user.id
        privacy = shop.get("privacy", "public")
        approved = shop.get("approved_users", [])
        if privacy == "private" and str(user_id) != str(shop['owner_id']) and user_id not in approved:
            pending = shop.get("pending_requests", [])
            kb = InlineKeyboardMarkup()
            if user_id in pending: kb.add(InlineKeyboardButton("⏳ Pending", callback_data="ignore"))
            else: kb.add(InlineKeyboardButton("✋ Request Access", callback_data=f"req_access_{shop_id}"))
            kb.add(InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu_return"))
            try: bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🔒 <b>Private Shop</b>", reply_markup=kb)
            except: bot.send_message(call.message.chat.id, "🔒 <b>Private Shop</b>", reply_markup=kb)
            return
        buyer_sessions[user_id] = {'page': 0, 'cat': None, 'sort': 'new', 'search': None}
        render_shop_list(bot, call, shop_id)

    def render_shop_list(bot, call, shop_id):
        user_id = call.from_user.id
        session = get_session(user_id)
        shop = get_shop(shop_id)
        all_products = []
        for pid, data in shop.get("products", {}).items():
            if session['cat'] and data.get("category") != session['cat']: continue
            if session['search'] and session['search'].lower() not in data['name'].lower(): continue
            all_products.append({'id': pid, **data})
        if session['sort'] == 'price_asc':
            all_products.sort(key=lambda x: float(x.get('price', 0)) if str(x.get('price',0)).replace('.','',1).isdigit() else 0)
        elif session['sort'] == 'price_desc':
            all_products.sort(key=lambda x: float(x.get('price', 0)) if str(x.get('price',0)).replace('.','',1).isdigit() else 0, reverse=True)
        elif session['sort'] == 'old':
            all_products.sort(key=lambda x: x['id'])
        else: 
            all_products.sort(key=lambda x: x['id'], reverse=True)
        total = len(all_products)
        start = session['page'] * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_items = all_products[start:end]
        kb = InlineKeyboardMarkup(row_width=2)
        for p in page_items:
            icon = "🔴" if p.get("status") == "sold" else "🟢"
            kb.add(InlineKeyboardButton(f"{icon} {p['name']} - {p['price']}", callback_data=f"sh_view_{shop_id}_{p['id']}"))
        nav = []
        if session['page'] > 0: nav.append(InlineKeyboardButton("⬅️", callback_data=f"buy_nav_{shop_id}_prev"))
        nav.append(InlineKeyboardButton(f"📄 {session['page']+1}", callback_data="ignore"))
        if end < total: nav.append(InlineKeyboardButton("➡️", callback_data=f"buy_nav_{shop_id}_next"))
        kb.row(*nav)
        filter_status = f"Cat: {shop.get('categories', {}).get(session['cat'], 'All')}" if session['cat'] else "📂 Cats"
        kb.row(InlineKeyboardButton(f"🔍 {session['search'] or 'Search'}", callback_data=f"buy_tool_{shop_id}_search"), InlineKeyboardButton(filter_status, callback_data=f"buy_tool_{shop_id}_cat"), InlineKeyboardButton("Sort", callback_data=f"buy_tool_{shop_id}_sort"))
        if session['cat'] or session['search']: kb.add(InlineKeyboardButton("❌ Clear Filters", callback_data=f"buy_tool_{shop_id}_clear"))
        kb.add(InlineKeyboardButton("❌ Close Shop", callback_data="main_menu_return"))
        text = f"🏪 <b>{shop['name']}</b>\n📦 <b>Products:</b> {total} found"
        try: bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        except: 
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("req_access_"))
    def handle_access_request(call):
        shop_id = call.data.replace("req_access_", "")
        user_info = {"first_name": call.from_user.first_name, "username": call.from_user.username or "None"}
        if add_access_request(shop_id, call.from_user.id, user_info):
            bot.answer_callback_query(call.id, "✅ Sent!", show_alert=True)
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("⏳ Pending", callback_data="ignore"), InlineKeyboardButton("🏠 Main", callback_data="main_menu_return"))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🔒 <b>Request Sent</b>", reply_markup=kb)
        else: bot.answer_callback_query(call.id, "❌ Error.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("buy_nav_"))
    def handle_nav(call):
        parts = call.data.split("_")
        shop_id, action = parts[2], parts[3]
        session = get_session(call.from_user.id)
        if action == "next": session['page'] += 1
        elif action == "prev" and session['page'] > 0: session['page'] -= 1
        render_shop_list(bot, call, shop_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("buy_tool_"))
    def handle_tools(call):
        parts = call.data.split("_")
        shop_id, tool = parts[2], parts[3]
        session = get_session(call.from_user.id)
        if tool == "sort":
            cycle = {'new': 'price_asc', 'price_asc': 'price_desc', 'price_desc': 'new'}
            session['sort'] = cycle.get(session['sort'], 'new')
            render_shop_list(bot, call, shop_id)
        elif tool == "clear":
            session['cat'] = None; session['search'] = None; session['page'] = 0
            render_shop_list(bot, call, shop_id)
        elif tool == "cat":
            shop = get_shop(shop_id)
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(InlineKeyboardButton("📦 All", callback_data=f"buy_setcat_{shop_id}_all"))
            for cid, cname in shop.get('categories', {}).items(): kb.add(InlineKeyboardButton(cname, callback_data=f"buy_setcat_{shop_id}_{cid}"))
            kb.add(InlineKeyboardButton("🔙 Back", callback_data=f"view_prods_{shop_id}"))
            bot.edit_message_text("📂 <b>Select Category:</b>", call.message.chat.id, call.message.message_id, reply_markup=kb)
        elif tool == "search":
            msg = bot.send_message(call.message.chat.id, "🔍 <b>Enter search keyword:</b>")
            bot.register_next_step_handler(msg, process_search, bot, shop_id, call)

    def process_search(message, bot, shop_id, original_call):
        session = get_session(message.from_user.id)
        session['search'] = message.text; session['page'] = 0
        try: bot.delete_message(message.chat.id, message.message_id); bot.delete_message(message.chat.id, message.message_id-1)
        except: pass
        render_shop_list(bot, original_call, shop_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("buy_setcat_"))
    def set_category(call):
        parts = call.data.split("_")
        shop_id, cat_id = parts[2], parts[3]
        session = get_session(call.from_user.id)
        session['cat'] = None if cat_id == "all" else cat_id
        session['page'] = 0
        render_shop_list(bot, call, shop_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("sh_view_"))
    def view_product(call):
        try:
            parts = call.data.split("_")
            shop_id, prod_id = parts[2], "_".join(parts[3:])
            shop = get_shop(shop_id)
            prod = shop["products"].get(prod_id)
            if not prod: return
            
            avg_rating, count_rating = get_product_rating(shop_id, prod_id)
            rating_txt = f"⭐ {avg_rating} ({count_rating} reviews)" if count_rating > 0 else "⭐ New"
            
            media_list = prod.get("media", [])
            if "image" in prod: media_list = [{"type": "photo", "file_id": prod["image"]}]
            use_thumbnail = prod.get("use_thumbnail", True)
            cat_tag = ""
            if prod.get("category"):
                cat_name = shop.get("categories", {}).get(prod["category"], "")
                if cat_name: cat_tag = f"\n🏷️ <b>#{cat_name}</b>"
            caption = (f"📦 <b>{prod['name']}</b>\n💰 <b>Price:</b> {prod['price']}\n{rating_txt}\n\n📝 <b>Description:</b>\n{prod.get('description', 'No desc')}{cat_tag}\n\n🏪 <b>Seller:</b> {shop['name']}")
            kb = InlineKeyboardMarkup()
            if use_thumbnail and len(media_list) > 1: kb.add(InlineKeyboardButton("📂 View Full Gallery", callback_data=f"sh_gallery_{shop_id}_{prod_id}"))
            if prod.get("status") == "sold": kb.add(InlineKeyboardButton("❌ SOLD OUT", callback_data="sh_alert_sold"))
            else: kb.add(InlineKeyboardButton("💬 Contact Seller to Buy", url=f"tg://user?id={shop_id}"))
            kb.add(InlineKeyboardButton(f"⭐ Reviews ({count_rating})", callback_data=f"view_revs_{shop_id}_{prod_id}"), InlineKeyboardButton("✍️ Rate", callback_data=f"rate_prod_{shop_id}_{prod_id}"))
            kb.add(InlineKeyboardButton("🔙 Back to List", callback_data=f"view_prods_{shop_id}"))
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            if use_thumbnail or len(media_list) == 1:
                m = media_list[0]
                if m["type"] == "photo": bot.send_photo(call.message.chat.id, m["file_id"], caption=caption, reply_markup=kb)
                else: bot.send_video(call.message.chat.id, m["file_id"], caption=caption, reply_markup=kb)
            else:
                album = []
                for m in media_list:
                    if m["type"] == "photo": album.append(InputMediaPhoto(m["file_id"]))
                    elif m["type"] == "video": album.append(InputMediaVideo(m["file_id"]))
                bot.send_media_group(call.message.chat.id, album)
                bot.send_message(call.message.chat.id, caption, reply_markup=kb)
        except: bot.send_message(call.message.chat.id, "❌ Error.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("sh_gallery_"))
    def view_full_gallery(call):
        try:
            parts = call.data.split("_")
            shop_id, prod_id = parts[2], "_".join(parts[3:])
            prod = get_shop(shop_id)["products"].get(prod_id)
            media_list = prod.get("media", [])
            album = []
            for m in media_list:
                if m["type"] == "photo": album.append(InputMediaPhoto(m["file_id"]))
                elif m["type"] == "video": album.append(InputMediaVideo(m["file_id"]))
            bot.answer_callback_query(call.id, "📂 Opening Gallery...")
            bot.send_media_group(call.message.chat.id, album)
        except: pass

    @bot.callback_query_handler(func=lambda c: c.data == "sh_alert_sold")
    def alert_sold(call):
        bot.answer_callback_query(call.id, "🚫 Sold out!", show_alert=True)
