import os
import traceback
from telebot import types
from .data import get_wm_settings, save_wm_settings
from .engine import apply_watermark_image, apply_watermark_video
from .menus import *

# 🛡️ Safe Import for Admin Check
try:
    from utils.utils import is_admin
except ImportError:
    def is_admin(uid): return False

FONTS_DIR = "data/fonts"
MAX_FONT_SIZE = 3 * 1024 * 1024
MAX_MEDIA_SIZE = 20 * 1024 * 1024

if not os.path.exists(FONTS_DIR): os.makedirs(FONTS_DIR)

user_states = {}
last_menu_ids = {}

def update_wm(cid, k, v): save_wm_settings(cid, k, v)

# --- Helper to Send/Edit Menu Safely ---
def send_menu(bot, cid, txt, mk, mid=None):
    if mid:
        try:
            bot.edit_message_text(txt, cid, mid, reply_markup=mk, parse_mode="Markdown")
            last_menu_ids[cid] = mid
            return
        except Exception:
            # যদি মেসেজ একই থাকে তবে টেলিগ্রাম এরর দেয়, আমরা সেটা ইগনোর করবো
            pass
            
    # যদি আগের মেনু ডিলিট করে নতুন পাঠাতে চাই
    if cid in last_menu_ids:
        try: bot.delete_message(cid, last_menu_ids[cid])
        except: pass
    
    try:
        sent = bot.send_message(cid, txt, reply_markup=mk, parse_mode="Markdown")
        last_menu_ids[cid] = sent.message_id
    except Exception as e:
        print(f"Send Menu Error: {e}")

def refresh_main_menu(bot, cid, mid=None):
    s = get_wm_settings(cid)
    txt = f"🎛️ **Watermark Studio**\n📝 Text: `{s.get('text','Watermark')}`\n🎨 Font: `{s.get('font_name','Default')}`\n👇 **Send Photo, Video or GIF to process.**"
    send_menu(bot, cid, txt, get_main_menu(s), mid)

# --- PROCESS MEDIA (Main Logic) ---
def process_media(bot, m, file_type):
    cid = m.chat.id
    msg = bot.reply_to(m, f"⏳ Processing {file_type.title()}... Please wait.")
    
    try:
        if file_type == 'photo': file_id = m.photo[-1].file_id
        elif file_type == 'video': file_id = m.video.file_id
        elif file_type == 'gif': file_id = m.animation.file_id

        file_info = bot.get_file(file_id)
        if file_info.file_size > MAX_MEDIA_SIZE:
            bot.delete_message(cid, msg.message_id)
            bot.reply_to(m, f"⚠️ File too big! Max size: {MAX_MEDIA_SIZE/(1024*1024):.0f}MB")
            return

        downloaded = bot.download_file(file_info.file_path)
        ext_in = ".mp4" if file_type == 'video' else (".gif" if file_type == 'gif' else ".jpg")
        
        t_in = f"ui_in_{cid}{ext_in}"
        t_out = f"ui_out_{cid}{ext_in}"
        
        with open(t_in, 'wb') as f: f.write(downloaded)
        
        s = get_wm_settings(cid)
        if file_type == 'photo':
            success = apply_watermark_image(t_in, t_out, s)
        else:
            bot.edit_message_text(f"🎬 Rendering {file_type.title()}... This may take time.", cid, msg.message_id)
            success = apply_watermark_video(t_in, t_out, s, is_gif=(file_type=='gif'))

        if success:
            bot.delete_message(cid, msg.message_id)
            with open(t_out, 'rb') as f:
                if file_type == 'photo': bot.send_photo(cid, f, caption="✅ Done")
                elif file_type == 'video': bot.send_video(cid, f, caption="✅ Done")
                elif file_type == 'gif': bot.send_animation(cid, f, caption="✅ Done")
        else:
            bot.edit_message_text("❌ Processing Failed (Engine Error).", cid, msg.message_id)

        if os.path.exists(t_in): os.remove(t_in)
        if os.path.exists(t_out): os.remove(t_out)
        refresh_main_menu(bot, cid)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {e}", cid, msg.message_id)
        if os.path.exists(t_in): os.remove(t_in)


# =========================================================
# 🎮 MAIN HANDLERS
# =========================================================

def register_watermark_handlers(bot):

    # -------------------------------------------------
    # HELPER: AUTO STOP LOADING SPINNER
    # -------------------------------------------------
    def safe_handle(call, func):
        try:
            bot.answer_callback_query(call.id) # 🛑 KEY FIX: STOPS LOADING
            func()
        except Exception as e:
            print(f"❌ Callback Error ({call.data}): {e}")
            traceback.print_exc()

    @bot.callback_query_handler(func=lambda c: c.data == "tool_img")
    def open_studio(c):
        def action():
            user_states[c.message.chat.id] = "waiting_media"
            refresh_main_menu(bot, c.message.chat.id, c.message.message_id)
        safe_handle(c, action)

    @bot.callback_query_handler(func=lambda c: c.data == "wm_menu_main")
    def back_main(c): 
        safe_handle(c, lambda: refresh_main_menu(bot, c.message.chat.id, c.message.message_id))

    # --- FONTS ---
    @bot.callback_query_handler(func=lambda c: c.data == "wm_menu_fonts")
    def m_fonts(c):
        safe_handle(c, lambda: send_menu(bot, c.message.chat.id, "🔠 **Font Manager**", get_font_menu(get_wm_settings(c.message.chat.id), c.from_user.id, "main"), c.message.message_id))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("wm_font_view_"))
    def v_fonts(c):
        def action():
            v = c.data.replace("wm_font_view_", "")
            t = "🌐 **Global Library**" if v=="all" else "❤️ **Favorites**"
            send_menu(bot, c.message.chat.id, t, get_font_menu(get_wm_settings(c.message.chat.id), c.from_user.id, v), c.message.message_id)
        safe_handle(c, action)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("wm_fset_"))
    def set_font(c):
        def action():
            fname = c.data.replace("wm_fset_", "")
            fpath = os.path.join(FONTS_DIR, fname)
            if os.path.exists(fpath):
                update_wm(c.message.chat.id, "font_name", fname)
                update_wm(c.message.chat.id, "font_path", fpath)
                update_wm(c.message.chat.id, "font_custom", True)
                
                # Show main font menu again
                send_menu(bot, c.message.chat.id, "🔠 **Font Manager**", get_font_menu(get_wm_settings(c.message.chat.id), c.from_user.id, "main"), c.message.message_id)
            else:
                bot.answer_callback_query(c.id, "⚠️ Missing File", show_alert=True)
        safe_handle(c, action)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("wm_ffav_"))
    def tog_fav(c):
        def action():
            fname = c.data.replace("wm_ffav_", "")
            s = get_wm_settings(c.message.chat.id); favs = s.get('favorites', [])
            if fname in favs: favs.remove(fname); msg="💔 Removed"
            else: favs.append(fname); msg="❤️ Added"
            update_wm(c.message.chat.id, "favorites", favs)
            
            # Show update alert but keep loading stopped
            bot.answer_callback_query(c.id, msg) 
            send_menu(bot, c.message.chat.id, "🌐 **Global Library**", get_font_menu(s, c.from_user.id, "all"), c.message.message_id)
        # Exceptionally manually handled inside action for custom alerts, but wrapping safely
        try: action() 
        except: pass

    @bot.callback_query_handler(func=lambda c: c.data.startswith("wm_fdel_"))
    def del_font(c):
        def action():
            if not is_admin(c.from_user.id): 
                bot.answer_callback_query(c.id, "⛔ Admins Only", show_alert=True)
                return
            fname = c.data.replace("wm_fdel_", "")
            try:
                os.remove(os.path.join(FONTS_DIR, fname))
                bot.answer_callback_query(c.id, "🗑️ Deleted")
                send_menu(bot, c.message.chat.id, "🌐 **Global Library**", get_font_menu(get_wm_settings(c.message.chat.id), c.from_user.id, "all"), c.message.message_id)
            except: pass
        safe_handle(c, action)

    @bot.callback_query_handler(func=lambda c: c.data == "wm_font_upload")
    def ask_f_up(c):
        def action():
            user_states[c.message.chat.id] = "waiting_font"
            # Delete old menu to avoid clutter
            if c.message.chat.id in last_menu_ids:
                try: bot.delete_message(c.message.chat.id, last_menu_ids[c.message.chat.id])
                except: pass
            msg = bot.send_message(c.message.chat.id, "📤 **Send .ttf/.otf file (Max 3MB):**")
            last_menu_ids[c.message.chat.id] = msg.message_id
        safe_handle(c, action)
    
    @bot.callback_query_handler(func=lambda c: c.data == "wm_font_set_default")
    def def_font(c):
        def action():
            update_wm(c.message.chat.id, "font_custom", False)
            update_wm(c.message.chat.id, "font_name", "Default")
            send_menu(bot, c.message.chat.id, "🔠 **Font Manager**", get_font_menu(get_wm_settings(c.message.chat.id), c.from_user.id, "main"), c.message.message_id)
        safe_handle(c, action)

    # --- PREVIEW ---
    @bot.callback_query_handler(func=lambda c: c.data == "wm_do_preview")
    def do_prev(c):
        # Preview takes time, so we explicitly answer first inside safe_handle
        def action():
            try:
                from PIL import Image
                t_in, t_out = f"p_in_{c.message.chat.id}.jpg", f"p_out_{c.message.chat.id}.jpg"
                Image.new('RGB', (1280, 720), (200, 200, 200)).save(t_in)
                apply_watermark_image(t_in, t_out, get_wm_settings(c.message.chat.id))
                with open(t_out, 'rb') as f: bot.send_photo(c.message.chat.id, f, caption="👁️ Image Preview")
                os.remove(t_in); os.remove(t_out)
                refresh_main_menu(bot, c.message.chat.id) # Show menu again
            except Exception as e:
                bot.send_message(c.message.chat.id, f"Preview Error: {e}")
        safe_handle(c, action)

    # --- OTHER TOGGLES ---
    @bot.callback_query_handler(func=lambda c: c.data == "wm_toggle_mode")
    def tog_m(c): 
        safe_handle(c, lambda: (update_wm(c.message.chat.id, "mode", 'logo' if get_wm_settings(c.message.chat.id).get('mode')=='text' else 'text'), refresh_main_menu(bot, c.message.chat.id, c.message.message_id)))

    # COLORS, STYLES, INPUTS - All wrapped with safe_handle logic implicitly
    # (To keep code short, I'll apply the pattern to the remaining groups)

    @bot.callback_query_handler(func=lambda c: c.data == "wm_menu_col_target")
    def m_col_t(c): safe_handle(c, lambda: send_menu(bot, c.message.chat.id, "🎨 **Select Target:**", get_color_target_menu(), c.message.message_id))
    
    @bot.callback_query_handler(func=lambda c: c.data.startswith("wm_col_menu_"))
    def m_col_p(c): safe_handle(c, lambda: send_menu(bot, c.message.chat.id, "🎨 **Pick Color:**", get_color_palette_menu(c.data.split("_")[-1]), c.message.message_id))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("wm_setcol_"))
    def set_col(c):
        def action():
            p = c.data.split("_"); t, v = p[2], p[3]
            if v == "cust": 
                user_states[c.message.chat.id] = f"waiting_col_{t}"
                if c.message.chat.id in last_menu_ids:
                    try: bot.delete_message(c.message.chat.id, last_menu_ids[c.message.chat.id])
                    except: pass
                msg = bot.send_message(c.message.chat.id, f"🎨 **Send Hex for {t}:**")
                last_menu_ids[c.message.chat.id] = msg.message_id
            else: 
                update_wm(c.message.chat.id, "text_color" if t=="text" else "bg_color", v)
                refresh_main_menu(bot, c.message.chat.id, c.message.message_id)
        safe_handle(c, action)

    @bot.callback_query_handler(func=lambda c: c.data == "wm_set_text")
    def ask_t(c):
        def action():
            user_states[c.message.chat.id] = "waiting_text"
            if c.message.chat.id in last_menu_ids:
                 try: bot.delete_message(c.message.chat.id, last_menu_ids[c.message.chat.id])
                 except: pass
            msg=bot.send_message(c.message.chat.id, "✍️ **Send Text:**")
            last_menu_ids[c.message.chat.id]=msg.message_id
        safe_handle(c, action)

    # Style, Tile, Logo handlers follow same pattern
    @bot.callback_query_handler(func=lambda c: c.data == "wm_menu_style")
    def m_style(c): safe_handle(c, lambda: send_menu(bot, c.message.chat.id, "✨ **Style**", get_style_menu(), c.message.message_id))
    
    @bot.callback_query_handler(func=lambda c: c.data == "wm_menu_tile")
    def m_tile(c): safe_handle(c, lambda: send_menu(bot, c.message.chat.id, "💠 **Layout**", get_tile_menu(get_wm_settings(c.message.chat.id)), c.message.message_id))

    @bot.callback_query_handler(func=lambda c: c.data == "wm_tog_bg")
    def tog_bg(c):
         safe_handle(c, lambda: (update_wm(c.message.chat.id, "bg_enabled", not get_wm_settings(c.message.chat.id).get('bg_enabled')), refresh_main_menu(bot, c.message.chat.id, c.message.message_id)))

    # ... (Any missing minor button handlers should just follow this safe_handle pattern) ...

    # --- INPUT LISTENERS (No change needed here, these are messages not callbacks) ---
    @bot.message_handler(content_types=['document'], func=lambda m: user_states.get(m.chat.id) == "waiting_font")
    def up_font(m):
        if not m.document.file_name.lower().endswith(('.ttf','.otf')): return bot.reply_to(m, "⚠️ Need .ttf/.otf")
        if m.document.file_size > MAX_FONT_SIZE: return bot.reply_to(m, "⚠️ Max 3MB")
        path = os.path.join(FONTS_DIR, m.document.file_name)
        if os.path.exists(path): return bot.reply_to(m, "⛔ Name taken!")
        try:
            with open(path, 'wb') as f: f.write(bot.download_file(bot.get_file(m.document.file_id).file_path))
            update_wm(m.chat.id, "font_name", m.document.file_name); update_wm(m.chat.id, "font_path", path); update_wm(m.chat.id, "font_custom", True)
            favs = get_wm_settings(m.chat.id).get('favorites', [])
            if m.document.file_name not in favs: favs.append(m.document.file_name); update_wm(m.chat.id, "favorites", favs)
            bot.reply_to(m, f"✅ Uploaded: {m.document.file_name}"); user_states[m.chat.id]="waiting_media"; refresh_main_menu(bot, m.chat.id)
        except Exception as e: bot.reply_to(m, f"Error: {e}")

    @bot.message_handler(content_types=['text', 'photo', 'video', 'animation', 'document'], func=lambda m: m.chat.type=='private')
    def handle_inp(m):
        st = user_states.get(m.chat.id)
        
        # Text Inputs
        if st == "waiting_text" and m.text: update_wm(m.chat.id, "text", m.text); user_states[m.chat.id]="waiting_media"; refresh_main_menu(bot, m.chat.id)
        elif st and st.startswith("waiting_col_") and m.text: update_wm(m.chat.id, "text_color" if "text" in st else "bg_color", m.text); user_states[m.chat.id]="waiting_media"; refresh_main_menu(bot, m.chat.id)
        
        # Media Inputs
        elif st == "waiting_media" or st is None:
            if m.photo: process_media(bot, m, 'photo')
            elif m.video: process_media(bot, m, 'video')
            elif m.animation: process_media(bot, m, 'gif')
            elif m.document and m.document.mime_type and m.document.mime_type.startswith('video'): process_media(bot, m, 'video')
