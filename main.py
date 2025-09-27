import json
import logging
import os # <-- os module add kiya, just in case aage zaroorat pade (though BOT_TOKEN in config.py handles this)
from config import BOT_TOKEN 
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- Global Variable for Admin IDs ---
# NameError theek karne ke liye isse global define kiya gaya hai
ADMIN_USER_IDS = [] 
# -------------------------------------

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration & Data Management ---
DATA_FILE = 'users_data.json'
ADMIN_IDS_FILE = 'admin_ids.json' # <-- Admin IDs file ka naam define kiya
DEFAULT_SETTINGS = {
    "leaderboard_size": 10,
    "leaderboard_header": "🏆 MONKXZ GLOBAL LEADERBOARD 🏆",    
    "support_message": "📞 **Support se Sampark Karein**\n\n**Aapko koi sawaal ya takleef hai, toh kripya seedhe hamare support team se sampark karein: @YourSupportUsername**",
    "start_message": "**Welcome! I AM MONKXZ LEADERBOARD BOT!!**\n\n**EARN TOGETHER !!**",
    "referral_points": 500
}

def load_admin_ids():
    """Admin IDs ko admin_ids.json file se load karta hai aur global variable set karta hai."""
    global ADMIN_USER_IDS
    try:
        with open(ADMIN_IDS_FILE, 'r') as f:
            data = json.load(f)
            
            # Assuming your JSON file has a key named "admin_ids" with a list of IDs (e.g., {"admin_ids": [12345, 67890]})
            if 'admin_ids' in data and isinstance(data['admin_ids'], list):
                # IDs ko integer mein convert karein
                ADMIN_USER_IDS = [int(id) for id in data['admin_ids']] 
                logger.info(f"Loaded {len(ADMIN_USER_IDS)} admin IDs.")
            else:
                logger.error(f"'{ADMIN_IDS_FILE}' is missing the 'admin_ids' key or it's not a list.")
                
    except FileNotFoundError:
        logger.error(f"'{ADMIN_IDS_FILE}' file not found! Admin features will not work.")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from '{ADMIN_IDS_FILE}'.")
    
# Baaki ke functions jismein koi change nahi hai...

def load_user_data():
    """Load user data and bot settings from JSON, applying defaults if missing."""
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            if "_settings" not in data:
                data["_settings"] = DEFAULT_SETTINGS
            else:
                for key, default_val in DEFAULT_SETTINGS.items():
                    if key not in data["_settings"]:
                         data["_settings"][key] = default_val
            return data
            
    except FileNotFoundError:
        return {"_settings": DEFAULT_SETTINGS}
    except json.JSONDecodeError:
        logger.error("Error decoding JSON from user_data.json. Returning empty data with defaults.")
        return {"_settings": DEFAULT_SETTINGS}

def save_user_data(data):
    """Save user data and settings to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_user_rank(user_id, data):
    """Calculates user's rank and points."""
    users_to_sort = {k: v for k, v in data.items() if k != "_settings"}
    
    sorted_users = sorted(
        [(uid, user.get('points', 0)) for uid, user in users_to_sort.items()],
        key=lambda item: item[1],
        reverse=True
    )
    
    rank = 0
    points = data.get(user_id, {}).get('points', 0)
    total_users = len(users_to_sort)
    
    last_points = -1
    for i, (uid, pts) in enumerate(sorted_users):
        if pts != last_points:
            current_rank = i + 1
        
        if str(uid) == str(user_id):
            rank = current_rank
            break
            
        last_points = pts
            
    return rank, points, total_users

def is_admin(user_id):
    """Checks if the given user_id is in the ADMIN_USER_IDS list."""
    return int(user_id) in ADMIN_USER_IDS

def grant_referral_points(referrer_id, new_user_id, data):
    """Grants referral points to the referrer and marks new user as referred."""
    settings = data.get("_settings", DEFAULT_SETTINGS)
    referral_points = settings.get("referral_points", 500)
    
    if referrer_id not in data or referrer_id == "_settings":
        return False, "Referrer not found"
        
    if data[new_user_id].get('referred', False):
        return False, "User already referred"
    
    current_points = data[referrer_id].get('points', 0)
    data[referrer_id]['points'] = current_points + referral_points
    
    data[new_user_id]['referred'] = True
    data[new_user_id]['referrer_id'] = referrer_id
    
    return True, referral_points

# --- Bot Commands ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command, showing the main Reply Keyboard, and checking referral."""
    
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    data = load_user_data()
    
    # --- Referral Logic Check ---
    if context.args:
        referrer_id = str(context.args[0])
        
        if user_id not in data or user_id == "_settings":
            data[user_id] = {'points': 0, 'username': update.effective_user.username or user_name, 'referred': False}

        if referrer_id != user_id and not data[user_id].get('referred', False):
            success, points = grant_referral_points(referrer_id, user_id, data)
            if success:
                save_user_data(data)
                
                await update.message.reply_text(
                    f"**🎉 Welcome! You joined via referral. Your referrer (ID: {referrer_id}) earned {points} points!**",
                    parse_mode='Markdown'
                )
    
    # Set default user data if not done via referral
    if user_id not in data or user_id == "_settings":
        data[user_id] = {'points': 0, 'username': update.effective_user.username or user_name}
        save_user_data(data)

    # --- Start Message & Keyboard ---
    custom_start_message = data["_settings"].get("start_message", DEFAULT_SETTINGS["start_message"])
    
    button_account = KeyboardButton("💳 My Account")
    button_leaderboard = KeyboardButton("🏆 Leaderboard")
    button_invite = KeyboardButton("🤝 Invite Friends")
    # Button name changed to Stats/Support
    button_support = KeyboardButton("📊 Stats/Support")
    
    keyboard_layout = [
        [button_account],
        [button_leaderboard, button_invite],
        [button_support]
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard_layout,    
        resize_keyboard=True,    
        one_time_keyboard=False    
    )
    
    await update.message.reply_text(
        f'{custom_start_message}',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def mypoints(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows user's points and rank."""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    data = load_user_data()

    if user_id not in data or data[user_id].get('points', 0) == 0:
        await (update.message or update.callback_query).reply_text(f"**Hi {user_name}! Aapke paas abhi koi points nahi hain. Shuru karo!**", parse_mode='Markdown')
        return

    rank, points, total_users = get_user_rank(user_id, data)

    await (update.message or update.callback_query).reply_text(
        f"**🏆 {user_name} ke Points:**\n"
        f"**Points:** {points}\n"    
        f"**Rank:** #{rank} out of {total_users} users.",
        parse_mode='Markdown'
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the customizable Top N users leaderboard."""
    data = load_user_data()
    
    users_to_sort = {k:v for k,v in data.items() if k != "_settings" and v.get('points', 0) > 0}
    
    if not users_to_sort:
        await (update.message or update.callback_query).reply_text("**Leaderboard abhi khali hai. Koi points add karo!**", parse_mode='Markdown')
        return
    
    settings = data.get("_settings", DEFAULT_SETTINGS)
    top_n = settings.get("leaderboard_size", 10)
    header = settings.get("leaderboard_header", DEFAULT_SETTINGS["leaderboard_header"])
    
    # Sort users: (UID, Points, Username)
    sorted_users = sorted(
        [(uid, user['points'], user.get('username', 'N/A')) for uid, user in users_to_sort.items()],
        key=lambda item: item[1],
        reverse=True
    )
    
    leaderboard_msg = f"{header} **(Top {top_n})**\n\n"
    
    current_rank = 0
    last_points = -1
    
    for i, (uid, points, username) in enumerate(sorted_users):
        if current_rank > top_n and points != last_points:
            break
        
        if points != last_points:
            current_rank = i + 1
        
        if current_rank > top_n:
            break

        user_mention = f"@{username}" if username != 'N/A' and username else f"**User ID:** `{uid}`"

        leaderboard_msg += f"**#{current_rank}. {user_mention} - {points} points**\n"
        last_points = points
        
    await (update.message or update.callback_query).reply_text(leaderboard_msg, parse_mode='Markdown')

# --- Admin Commands ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the Admin Panel with settings and action options."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 **Access Denied: Yeh command sirf Admins ke liye hai.**", parse_mode='Markdown')
        return

    data = load_user_data()
    settings = data.get("_settings", DEFAULT_SETTINGS)
    current_size = settings.get("leaderboard_size", 10)
    current_header = settings.get("leaderboard_header", DEFAULT_SETTINGS["leaderboard_header"])
    current_support_msg_preview = settings.get("support_message", DEFAULT_SETTINGS["support_message"])[:20].replace('\n', ' ')
    current_start_msg_preview = settings.get("start_message", DEFAULT_SETTINGS["start_message"])[:20].replace('\n', ' ')
    current_referral_points = settings.get("referral_points", 500)
    
    btn_add = KeyboardButton("➕ Add Points")
    btn_remove = KeyboardButton("➖ Remove Points")
    btn_size = KeyboardButton(f"📐 Size: {current_size}")
    btn_header = KeyboardButton(f"📝 Header: {current_header[:20]}...")
    btn_support_msg = KeyboardButton(f"💬 Support Message: {current_support_msg_preview}...")
    btn_start_msg = KeyboardButton(f"⭐ Start Message: {current_start_msg_preview}...")
    btn_referral_points = KeyboardButton(f"💰 Referral Points: {current_referral_points}")
    btn_broadcast = KeyboardButton("📢 Broadcast Message") # Broadcast Button Added
    btn_back = KeyboardButton("🔙 Close Admin Panel")
    
    admin_keyboard = ReplyKeyboardMarkup(
        [
            [btn_add, btn_remove, btn_broadcast], # Broadcast added here
            [btn_size, btn_referral_points],
            [btn_header],
            [btn_support_msg],
            [btn_start_msg],
            [btn_back]
        ],    
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await update.message.reply_text(
        "👑 **Admin Panel**\n\n**Neeche diye gaye options se bot settings aur actions manage karein.**",
        reply_markup=admin_keyboard,
        parse_mode='Markdown'
    )

async def add_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin only: Adds points to a user. Format: /add <userid> <amount>"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 **Access Denied: Yeh command sirf Admins ke liye hai.**", parse_mode='Markdown')
        return

    try:
        if len(context.args) != 2:
            await update.message.reply_text("⚠️ **Sahi format:** `/add <user_id> <amount>`", parse_mode='Markdown')
            return
            
        target_user_id = str(context.args[0])
        amount = int(context.args[1])
        if amount <= 0:
            await update.message.reply_text("**Points 0 se zyada hone chahiye.**", parse_mode='Markdown')
            return

    except ValueError:
        await update.message.reply_text("⚠️ **User ID aur Amount integers hone chahiye.**", parse_mode='Markdown')
        return

    data = load_user_data()

    if target_user_id not in data or target_user_id == "_settings":
        data[target_user_id] = {'points': 0, 'username': 'N/A'}
        
        if update.effective_chat.type in ['group', 'supergroup', 'private']:
             try:
                chat_member = await context.bot.get_chat_member(update.effective_chat.id, target_user_id)
                if chat_member.user.username:
                     data[target_user_id]['username'] = chat_member.user.username
                elif chat_member.user.first_name:
                     data[target_user_id]['username'] = chat_member.user.first_name
             except Exception:
                pass

    data[target_user_id]['points'] = data[target_user_id].get('points', 0) + amount
    save_user_data(data)

    await update.message.reply_text(
        f"✅ **{amount} points successfully added to user {target_user_id}.**\n"
        f"**New Total: {data[target_user_id]['points']}**"
        , parse_mode='Markdown'
    )

async def remove_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin only: Removes points from a user. Format: /remove <userid> <amount>"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 **Access Denied: Yeh command sirf Admins ke liye hai.**", parse_mode='Markdown')
        return

    try:
        if len(context.args) != 2:
            await update.message.reply_text("⚠️ **Sahi format:** `/remove <user_id> <amount>`", parse_mode='Markdown')
            return
            
        target_user_id = str(context.args[0])
        amount = int(context.args[1])
        if amount <= 0:
            await update.message.reply_text("**Points 0 se zyada hone chahiye.**", parse_mode='Markdown')
            return

    except ValueError:
        await update.message.reply_text("⚠️ **User ID aur Amount integers hone chahiye.**", parse_mode='Markdown')
        return

    data = load_user_data()

    if target_user_id not in data or target_user_id == "_settings" or data[target_user_id].get('points', 0) == 0:
        await update.message.reply_text(f"⚠️ **User {target_user_id} ke paas koi points nahi hain ya exist nahi karta.**", parse_mode='Markdown')
        return

    current_points = data[target_user_id].get('points', 0)
    data[target_user_id]['points'] = max(0, current_points - amount)
    save_user_data(data)
    
    removed = current_points - data[target_user_id]['points']
    
    if removed > 0:
        await update.message.reply_text(
            f"✅ **{removed} points removed from user {target_user_id}.**\n"
            f"**New Total: {data[target_user_id]['points']}**"
            , parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"✅ **User {target_user_id} ke paas sirf {current_points} points the. Ab Total 0.**", parse_mode='Markdown')


async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin only: Shows info of any user. Format: /info <userid>"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 **Access Denied: Yeh command sirf Admins ke liye hai.**", parse_mode='Markdown')
        return

    if not context.args or len(context.args) > 1:
        await update.message.reply_text("⚠️ **Sahi format:** `/info <user_id>`", parse_mode='Markdown')
        return

    target_user_id = str(context.args[0])
    data = load_user_data()

    if target_user_id not in data or target_user_id == "_settings":
        await update.message.reply_text(f"⚠️ **User ID {target_user_id} ka data nahi mila.**", parse_mode='Markdown')
        return

    user_data = data[target_user_id]
    rank, points, total_users = get_user_rank(target_user_id, data)
    
    info_msg = (
        f"🕵️‍♂️ **User Info (Admin View)**\n\n"
        f"**User ID:** `{target_user_id}`\n"
        f"**Username:** {user_data.get('username', 'N/A')}\n"
        f"**Points:** {points}\n"
        f"**Rank:** #{rank} out of {total_users}"
    )

    await update.message.reply_text(info_msg, parse_mode='Markdown')


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin only: Sends a broadcast message to all users. Format: /broadcast <message>"""
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("⚠️ **Sahi format:** `/broadcast <message>`\n\n**Aap Admin Panel mein '📢 Broadcast Message' button se bhi message set kar sakte hain.**", parse_mode='Markdown')
        return

    message_to_send = " ".join(context.args)
    data = load_user_data()
    users = [uid for uid in data.keys() if uid != "_settings"]
    success_count = 0
    fail_count = 0

    await update.message.reply_text(f"📢 **Broadcast shuru! Total {len(users)} users ko message bheja ja raha hai.**", parse_mode='Markdown')
    
    for user_id in users:
        try:
            # Broadcast message ko automatic bold nahi rakhenge, taaki Admin apne hisaab se format kar sake
            await context.bot.send_message(chat_id=user_id, text=message_to_send, parse_mode='Markdown')
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user_id}: {e}")
            fail_count += 1

    await update.message.reply_text(
        f"✅ **Broadcast Samapt!**\n"
        f"**Successful Sends:** {success_count}\n"
        f"**Failed Sends:** {fail_count}",
        parse_mode='Markdown'
    )

# --- Reply Button Handlers ---

async def handle_account_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'My Account' button click logic."""
    await mypoints(update, context)

async def handle_leaderboard_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'Leaderboard' button click logic."""
    await leaderboard(update, context)

async def handle_invite_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'Invite Friends' button click logic, showing custom points and referral link."""
    
    user_id = update.effective_user.id
    data = load_user_data()
    referral_points = data["_settings"].get("referral_points", 500)
    
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username
    
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    await update.message.reply_text(
        "🤝 **Apne doston ko invite karein!**\n\n"
        f"**Aapke referral link se join hone waale har dost par aapko +{referral_points} points milenge.**\n\n"
        f"**🔗 Aapka Referral Link:**\n`{referral_link}`\n\n"
        "**Link ko copy karein aur apne doston ke saath share karein!**",
        parse_mode='Markdown'
    )

async def handle_stats_support_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'Stats/Support' button click logic, showing stats and custom message."""
    data = load_user_data()
    users_to_sort = {k: v for k, v in data.items() if k != "_settings"}
    
    total_users = len(users_to_sort)
    total_points = sum(user.get('points', 0) for user in users_to_sort.values())
    
    custom_message = data["_settings"].get("support_message", DEFAULT_SETTINGS["support_message"])
    
    stats_msg = (
        f"📊 **MONKXZ Bot Statistics**\n\n"
        f"**Total Users in Bot:** {total_users}\n"
        f"**Total Points Won:** {total_points}\n\n"
        "---" # Separator
    )
    
    # Custom message ko stats ke neeche append kiya jaayega
    final_message = stats_msg + "\n" + custom_message
    
    await update.message.reply_text(
        final_message,
        parse_mode='Markdown'
    )
    
# --- Admin Panel State Handler ---

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all admin button clicks and setting value inputs."""
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text
    data = load_user_data()
    
    # 1. Action Button Clicks
    if text == "➕ Add Points":
        await update.message.reply_text(
            "➕ **Points Add Karne ke liye:**\n"
            "**Kripya neeche diye gaye format mein command bhejein:**\n"
            "`/add <user_id> <amount>`\n"
            "**Example:** `/add 12345678 1000`",
            parse_mode='Markdown'
        )
        return
    elif text == "➖ Remove Points":
        await update.message.reply_text(
            "➖ **Points Remove Karne ke liye:**\n"
            "**Kripya neeche diye gaye format mein command bhejein:**\n"
            "`/remove <user_id> <amount>`\n"
            "**Example:** `/remove 12345678 500`",
            parse_mode='Markdown'
        )
        return
    elif text == "📢 Broadcast Message":
        context.user_data['setting_mode'] = 'broadcast'
        await update.message.reply_text(
            "📢 **Broadcast Message**\n\n"
            "**Kripya woh message bhejein jo aap sabhi users ko bhejna chahte hain (Markdown allowed hai):**\n"
            "**Ya phir, command use karein:** `/broadcast <message>`",
            parse_mode='Markdown'
        )
        return

    # 2. Settings Button Clicks
    elif text.startswith("📐 Size:"):
        context.user_data['setting_mode'] = 'size'
        await update.message.reply_text("**🔢 Leaderboard mein kitne users dikhane hain? Naya size (number) bhejein:**", parse_mode='Markdown')
        
    elif text.startswith("📝 Header:"):
        context.user_data['setting_mode'] = 'header'
        await update.message.reply_text("**📝 Leaderboard ke liye naya header text bhejein (max 50 chars):**", parse_mode='Markdown')
        
    elif text.startswith("💬 Support Message:"):
        context.user_data['setting_mode'] = 'support'
        current_msg = data["_settings"].get("support_message", "Default")
        await update.message.reply_text(
            f"💬 **Support Message Customization**\n\n"
            f"**Current Message:**\n`{current_msg}`\n\n"
            "**Naya support message bhejein (Markdown allowed hai):**"
        , parse_mode='Markdown')
        
    elif text.startswith("⭐ Start Message:"):
        context.user_data['setting_mode'] = 'start_msg'
        current_msg = data["_settings"].get("start_message", "Default")
        await update.message.reply_text(
            f"⭐ **Start Message Customization**\n\n"
            f"**Current Message:**\n`{current_msg}`\n\n"
            "**Naya start message bhejein (Markdown allowed hai):**"
        , parse_mode='Markdown')

    elif text.startswith("💰 Referral Points:"):
        context.user_data['setting_mode'] = 'referral'
        await update.message.reply_text("**💰 Naye Referral Points (number) bhejein. Ye points har invite par milenge:**", parse_mode='Markdown')
        
    elif text == "🔙 Close Admin Panel":
        await start(update, context)
        context.user_data.pop('setting_mode', None)
        
    # 3. Value Input (If in setting mode)
    elif 'setting_mode' in context.user_data:
        mode = context.user_data['setting_mode']

        if mode == 'broadcast':
            context.args = [text] # Input ko /broadcast command ki tarah process karein
            await broadcast(update, context)
            context.user_data.pop('setting_mode', None)
            await admin_panel(update, context)
            return
        
        elif mode == 'referral':
            try:
                new_points = int(text)
                if new_points < 0:
                    await update.message.reply_text("⚠️ **Points negative nahi ho sakte. Dobara try karein.**", parse_mode='Markdown')
                    return
                data["_settings"]["referral_points"] = new_points
                await update.message.reply_text(f"✅ **Referral Points successfully set to {new_points}.**", parse_mode='Markdown')
            except ValueError:
                await update.message.reply_text("⚠️ **Yeh valid number nahi hai. Dobara try karein.**", parse_mode='Markdown')

        elif mode == 'start_msg':
            new_message = text
            if len(new_message) > 500:
                await update.message.reply_text("⚠️ **Message bahut lamba hai (max 500 characters). Dobara try karein.**", parse_mode='Markdown')
                return
            data["_settings"]["start_message"] = new_message
            await update.message.reply_text(f"✅ **Start Message successfully updated. Naya Message:\n{new_message}**", parse_mode='Markdown')
            
        elif mode == 'size':
            try:
                new_size = int(text)
                if new_size <= 0 or new_size > 50:
                    await update.message.reply_text("⚠️ **Size 1 se 50 ke beech mein hona chahiye. Dobara try karein.**", parse_mode='Markdown')
                    return
                data["_settings"]["leaderboard_size"] = new_size
                await update.message.reply_text(f"✅ **Leaderboard Size successfully set to {new_size}.**", parse_mode='Markdown')
            except ValueError:
                await update.message.reply_text("⚠️ **Yeh valid number nahi hai. Dobara try karein.**", parse_mode='Markdown')

        elif mode == 'header':
            if len(text) > 50:
                await update.message.reply_text("⚠️ **Header bahut lamba hai (max 50 characters). Dobara try karein.**", parse_mode='Markdown')
                return
            data["_settings"]["leaderboard_header"] = text
            await update.message.reply_text(f"✅ **Leaderboard Header successfully set to: {text}**", parse_mode='Markdown')

        elif mode == 'support':
            if len(text) > 500:
                await update.message.reply_text("⚠️ **Message bahut lamba hai (max 500 characters). Dobara try karein.**", parse_mode='Markdown')
                return
            data["_settings"]["support_message"] = text
            await update.message.reply_text(f"✅ **Support Message successfully updated. Naya Message:\n{text}**", parse_mode='Markdown')

        save_user_data(data)
        context.user_data.pop('setting_mode', None)
        await admin_panel(update, context)    

    else:
        pass

# --- Main Application Setup ---

def main() -> None:
    """Starts the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Command Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mypoints", mypoints))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("add", add_points))
    application.add_handler(CommandHandler("remove", remove_points))
    application.add_handler(CommandHandler("info", user_info))
    application.add_handler(CommandHandler("broadcast", broadcast)) # Broadcast command handler

    # --- Reply Button Handlers ---
    application.add_handler(MessageHandler(filters.Regex(r'💳 My Account'), handle_account_button))
    application.add_handler(MessageHandler(filters.Regex(r'🏆 Leaderboard'), handle_leaderboard_button))
    application.add_handler(MessageHandler(filters.Regex(r'🤝 Invite Friends'), handle_invite_button))
    # Handler updated for the new button name
    application.add_handler(MessageHandler(filters.Regex(r'📊 Stats/Support'), handle_stats_support_button))
    
    # Admin Panel Buttons & Input
    # Regex updated to include the new Broadcast button
    admin_regex = filters.Regex(r'➕ Add Points|➖ Remove Points|📢 Broadcast Message|📐 Size:|📝 Header:|💬 Support Message:|⭐ Start Message:|💰 Referral Points:|🔙 Close Admin Panel')
    application.add_handler(MessageHandler(admin_regex, handle_admin_buttons))
    
    # Message handler for catching text input in admin mode (like setting values or broadcast message)
    # Note: filters.User(ADMIN_USER_IDS) will now work because ADMIN_USER_IDS is globally defined and loaded.
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & filters.User(ADMIN_USER_IDS), handle_admin_buttons))

    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    load_admin_ids() # <--- IDs ko load karein Taki main() mein woh available ho
    main()



