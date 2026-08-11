#!/usr/bin/env python3
"""
Law of Attraction Bot - Telegram
Full featured manifestation & mindset bot + OpenAI Chat Coach
"""

import logging
import os
from datetime import time
from typing import Optional, List, Dict

# Load .env file (if present) — API keys yahan se aayengi
from dotenv import load_dotenv
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from telegram.constants import ParseMode

import database as db
from affirmations import (
    generate_affirmation as local_generate_affirmation,
    get_visualization_prompt,
    get_gratitude_prompt,
    get_daily_message as local_get_daily_message,
)
import ai

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_GOAL, WAITING_GRATITUDE, WAITING_CATEGORY = range(3)

# Bot token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")

# In-memory chat history per user (last few messages) — for production use Redis/DB
chat_histories: Dict[int, List[Dict]] = {}


# ==================== KEYBOARDS ====================

def main_keyboard():
    keyboard = [
        [KeyboardButton("✨ Affirmation"), KeyboardButton("🎯 My Goals")],
        [KeyboardButton("🙏 Gratitude"), KeyboardButton("🧘 Visualize")],
        [KeyboardButton("💬 Chat with Coach"), KeyboardButton("🔥 Streak")],
        [KeyboardButton("💎 Premium"), KeyboardButton("⚙️ Settings")],
        [KeyboardButton("ℹ️ Help")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def goals_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Naya Goal Add Karo", callback_data="add_goal")],
        [InlineKeyboardButton("📋 Goals Dekho", callback_data="list_goals")],
        [InlineKeyboardButton("❌ Goal Complete / Remove", callback_data="remove_goal")],
    ]
    return InlineKeyboardMarkup(keyboard)


def category_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("💰 Money", callback_data="cat_money"),
            InlineKeyboardButton("❤️ Love", callback_data="cat_love"),
        ],
        [
            InlineKeyboardButton("💪 Health", callback_data="cat_health"),
            InlineKeyboardButton("💼 Career", callback_data="cat_career"),
        ],
        [InlineKeyboardButton("🌟 General", callback_data="cat_general")],
    ]
    return InlineKeyboardMarkup(keyboard)


def daily_keyboard(enabled: bool):
    if enabled:
        btn = InlineKeyboardButton("🔕 Daily Messages Off Karo", callback_data="daily_off")
    else:
        btn = InlineKeyboardButton("🔔 Daily Messages On Karo", callback_data="daily_on")
    return InlineKeyboardMarkup([[btn]])


# ==================== HELPERS ====================

def get_user_goals_texts(user_id: int) -> List[str]:
    goals = db.get_active_goals(user_id)
    return [g["goal_text"] for g in goals]


def get_recent_gratitude_texts(user_id: int, limit: int = 3) -> List[str]:
    entries = db.get_recent_gratitude(user_id, limit=limit)
    return [e["entry_text"] for e in entries]


def append_to_history(user_id: int, role: str, content: str):
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    chat_histories[user_id].append({"role": role, "content": content})
    # Keep only last 8 messages
    chat_histories[user_id] = chat_histories[user_id][-8:]


# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username, user.first_name)

    ai_status = f"✅ AI Coach {ai.get_provider_info()}" if ai.is_ai_available() else "⚠️ AI Coach OFF (API key nahi hai)"

    welcome = f"""
🌟 *Namaste {user.first_name}!* 🌟

Main tumhara *Law of Attraction Bot* + *AI Coach* hoon.

Main tumhe help karunga:
• Daily powerful affirmations
• Goals set karne aur track karne mein
• Gratitude practice
• Visualization
• Consistency (streak)
• **Free chat with AI Manifestation Coach** 💬

*AI Status:* {ai_status}

*Shuruaat:*
1. Goal set karo → /setgoal
2. Roz gratitude → /gratitude
3. Affirmation lo → /affirmation
4. Coach se baat karo → /chat ya "Chat with Coach" button

Neeche buttons se sab access kar sakte ho 👇
"""
    await update.message.reply_text(
        welcome,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ai_line = ""
    if ai.is_ai_available():
        ai_line = "\n/chat - AI Coach se free baat karo (sabse powerful feature)"
    else:
        ai_line = "\n/chat - AI Coach (abhi API key set nahi hai)"

    help_text = f"""
📖 *Law of Attraction Bot - Commands*

/start - Bot shuru karo
/affirmation - Aaj ka powerful affirmation
/setgoal - Naya goal / desire add karo
/mygoals - Apne saare active goals dekho
/gratitude - Aaj ki gratitude likho
/visualize - Guided visualization prompt
/streak - Apni consistency streak dekho
/daily - Daily morning messages on/off
/settings - Settings
/chat - AI Manifestation Coach se baat karo
/clear - Chat history clear karo
/help - Yeh message
{ai_line}

*Tips:*
• Goals present-tense mein likho
• Roz gratitude + affirmation karo
• AI Coach se freely baat karo — feelings, blocks, doubts sab share kar sakte ho
• Consistency sabse important hai 🔥
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def affirmation_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username, user.first_name)

    # Free limit check
    allowed, msg = db.can_use_affirmation(user.id)
    if not allowed:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    goals = get_user_goals_texts(user.id)
    affirmation = None

    # Try AI first
    if ai.is_ai_available():
        affirmation = ai.generate_ai_affirmation(
            goals=goals,
            user_name=user.first_name
        )

    # Fallback to local
    if not affirmation:
        affirmation = local_generate_affirmation(goals)

    db.log_affirmation(user.id, affirmation)

    text = f"""
✨ *Aaj ka Affirmation*

_{affirmation}_

---
Isse 3 baar zor se (ya mind mein) bolo.
Feel karo ki yeh already true hai.
"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def visualize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = get_visualization_prompt()
    text = f"""
🧘 *Guided Visualization*

{prompt}

*Kaise karein:*
1. Shant jagah baitho
2. Aankhein band karo
3. 1-3 minute ke liye deeply feel karo
4. Jab ready ho, aankhein kholo aur smile karo
"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def streak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username, user.first_name)
    u = db.get_user(user.id)
    streak = u["streak"] if u else 0

    if streak == 0:
        msg = "Abhi streak 0 hai. Aaj se shuru karo!\n\n/gratitude ya /affirmation use karke streak badhao 🔥"
    elif streak < 7:
        msg = f"🔥 *Current Streak: {streak} days*\n\nBahut badhiya! 7 din pure karo for first milestone."
    elif streak < 21:
        msg = f"🔥 *Current Streak: {streak} days*\n\nAmazing! 21-day habit banane ke kareeb ho."
    else:
        msg = f"🔥 *Current Streak: {streak} days*\n\nUnstoppable! Tumhara mindset strong ho chuka hai 💪"

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


async def mygoals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username, user.first_name)
    goals = db.get_active_goals(user.id)

    if not goals:
        text = "Abhi koi active goal nahi hai.\n\n/setgoal se apna pehla desire add karo 🎯"
    else:
        lines = [f"{i+1}. *{g['goal_text']}* ({g['category']})" for i, g in enumerate(goals)]
        text = "🎯 *Aapke Active Goals:*\n\n" + "\n".join(lines)

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=goals_keyboard()
    )


# ==================== CHAT WITH AI COACH ====================

async def chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enter chat mode or show status."""
    user = update.effective_user
    db.ensure_user(user.id, user.username, user.first_name)

    if not ai.is_ai_available():
        await update.message.reply_text(
            "⚠️ *AI Coach abhi available nahi hai.*\n\n"
            "OPENAI_API_KEY environment variable set nahi hai.\n"
            "Admin se key add karke bot restart karne ko bolo.\n\n"
            "Tab tak /affirmation, /gratitude, /visualize use kar sakte ho.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_keyboard()
        )
        return

    # Mark that user is in free chat mode
    context.user_data["chat_mode"] = True

    await update.message.reply_text(
        "💬 *AI Manifestation Coach ready hai!*\n\n"
        "Ab freely baat karo — feelings, doubts, goals, blocks, kuch bhi.\n"
        "Main tumhari madad karunga mindset shift aur clarity mein.\n\n"
        "Chat band karne ke liye /stopchat ya /clear likho.\n"
        "History clear karne ke liye /clear.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )


async def stopchat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["chat_mode"] = False
    await update.message.reply_text(
        "Chat mode band ho gaya. Normal commands use kar sakte ho.",
        reply_markup=main_keyboard()
    )


async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_histories.pop(user_id, None)
    context.user_data["chat_mode"] = False
    await update.message.reply_text(
        "🧹 Chat history clear ho gayi. Fresh start!",
        reply_markup=main_keyboard()
    )


async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process a free-form message with the AI coach."""
    user = update.effective_user
    user_id = user.id

    # Free limit check
    allowed, msg = db.can_use_chat(user_id)
    if not allowed:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    # Show typing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    goals = get_user_goals_texts(user_id)
    gratitude = get_recent_gratitude_texts(user_id)
    u = db.get_user(user_id)
    streak = u["streak"] if u else 0

    history = chat_histories.get(user_id, [])

    reply = ai.chat_with_coach(
        user_message=text,
        goals=goals,
        recent_gratitude=gratitude,
        streak=streak,
        chat_history=history,
        user_name=user.first_name,
    )

    # Count usage (only for free users effectively)
    db.increment_usage(user_id, "chat")

    # Save to history
    append_to_history(user_id, "user", text)
    append_to_history(user_id, "assistant", reply)

    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


# ==================== GOAL CONVERSATION ====================

async def setgoal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username, user.first_name)
    context.user_data["chat_mode"] = False  # exit chat mode

    # Goal limit check
    allowed, msg = db.can_add_goal(user.id)
    if not allowed:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    await update.message.reply_text(
        "🎯 *Naya Goal / Desire*\n\n"
        "Apna goal *present tense* mein likho.\n"
        "Example:\n"
        "• Main financially free hoon aur abundance attract karta hoon\n"
        "• Main healthy aur energetic body rakhta/rakhti hoon\n"
        "• Main apne dream job mein successful hoon\n\n"
        "Ab apna goal type karo:",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_GOAL


async def receive_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal_text = update.message.text.strip()
    if len(goal_text) < 5:
        await update.message.reply_text("Thoda detail mein likho (kam se kam 5 characters).")
        return WAITING_GOAL

    context.user_data["temp_goal"] = goal_text
    await update.message.reply_text(
        "Category choose karo:",
        reply_markup=category_keyboard()
    )
    return WAITING_CATEGORY


async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat = query.data.replace("cat_", "")
    goal_text = context.user_data.get("temp_goal")
    if not goal_text:
        await query.edit_message_text("Kuch error ho gaya. /setgoal se phir se try karo.")
        return ConversationHandler.END

    user_id = query.from_user.id
    goal_id = db.add_goal(user_id, goal_text, cat)

    await query.edit_message_text(
        f"✅ Goal add ho gaya!\n\n"
        f"*Goal:* {goal_text}\n"
        f"*Category:* {cat}\n"
        f"*ID:* {goal_id}\n\n"
        f"Ab /affirmation lo — yeh goal ke hisaab se personalize hoga.\n"
        f"Ya /chat karke AI Coach se is goal pe baat karo."
    )
    context.user_data.pop("temp_goal", None)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=main_keyboard())
    return ConversationHandler.END


# ==================== GRATITUDE ====================

async def gratitude_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username, user.first_name)
    context.user_data["chat_mode"] = False

    prompt = get_gratitude_prompt()
    await update.message.reply_text(
        f"🙏 *Gratitude Time*\n\n{prompt}\n\n"
        "Apni 1-3 cheezein likho (ek message mein):",
        parse_mode=ParseMode.MARKDOWN
    )
    return WAITING_GRATITUDE


async def receive_gratitude(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) < 3:
        await update.message.reply_text("Thoda aur likho please.")
        return WAITING_GRATITUDE

    user = update.effective_user
    db.add_gratitude(user.id, text)
    streak = db.get_user(user.id)["streak"]

    await update.message.reply_text(
        f"✅ Gratitude save ho gayi!\n\n"
        f"🔥 Current streak: *{streak} days*\n\n"
        f"Bahut badhiya. Gratitude practice se vibration high rehti hai.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


# ==================== SETTINGS & DAILY ====================

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username, user.first_name)
    u = db.get_user(user.id)
    enabled = bool(u["daily_enabled"]) if u else False
    ai_status = ai.get_provider_info() if ai.is_ai_available() else "OFF ❌ (API key missing)"

    status = "ON ✅" if enabled else "OFF ❌"
    text = f"""
⚙️ *Settings*

Daily Morning Messages: *{status}*
AI Coach: *{ai_status}*
Time: ~08:00 (server time)

Daily message mein milta hai:
• Personalized affirmation (AI se agar available ho)
• Visualization prompt
• Aapke goals
• Streak update
"""
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=daily_keyboard(enabled)
    )


async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await settings_cmd(update, context)


async def daily_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "daily_on":
        db.set_daily(user_id, True)
        await query.edit_message_text(
            "✅ Daily morning messages *ON* kar diye gaye!\n\n"
            "Har din subah affirmation + visualization milega.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif query.data == "daily_off":
        db.set_daily(user_id, False)
        await query.edit_message_text(
            "🔕 Daily messages *OFF* kar diye gaye.",
            parse_mode=ParseMode.MARKDOWN
        )


# ==================== INLINE CALLBACKS FOR GOALS ====================

async def goals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "add_goal":
        await query.edit_message_text(
            "🎯 Naya goal add karne ke liye /setgoal command use karo."
        )
    elif query.data == "list_goals":
        goals = db.get_active_goals(user_id)
        if not goals:
            await query.edit_message_text("Koi active goal nahi hai.")
        else:
            lines = [f"{i+1}. {g['goal_text']} ({g['category']}) — ID: {g['id']}" for i, g in enumerate(goals)]
            await query.edit_message_text("🎯 Active Goals:\n\n" + "\n".join(lines))
    elif query.data == "remove_goal":
        goals = db.get_active_goals(user_id)
        if not goals:
            await query.edit_message_text("Koi goal nahi hai remove karne ke liye.")
            return
        buttons = [
            [InlineKeyboardButton(f"❌ {g['goal_text'][:30]}", callback_data=f"delgoal_{g['id']}")]
            for g in goals[:8]
        ]
        await query.edit_message_text(
            "Kaunsa goal remove / complete karna hai?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif query.data.startswith("delgoal_"):
        goal_id = int(query.data.replace("delgoal_", ""))
        success = db.deactivate_goal(user_id, goal_id)
        if success:
            await query.edit_message_text("✅ Goal remove / complete ho gaya!")
        else:
            await query.edit_message_text("Goal nahi mila.")


# ==================== TEXT MESSAGE HANDLER ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lower = text.lower()

    # Keyboard button matches
    if "affirmation" in lower:
        await affirmation_cmd(update, context)
        return
    if "goal" in lower and "chat" not in lower:
        await mygoals_cmd(update, context)
        return
    if "gratitude" in lower:
        # This will be caught by ConversationHandler usually
        await gratitude_start(update, context)
        return
    if "visualize" in lower or "visual" in lower:
        await visualize_cmd(update, context)
        return
    if "streak" in lower:
        await streak_cmd(update, context)
        return
    if "setting" in lower:
        await settings_cmd(update, context)
        return
    if "help" in lower:
        await help_command(update, context)
        return
    if "chat with coach" in lower or lower == "chat":
        await chat_cmd(update, context)
        return
    if "premium" in lower or "subscribe" in lower:
        await premium_cmd(update, context)
        return

    # If user is in chat mode OR message looks like a normal conversation → AI
    in_chat_mode = context.user_data.get("chat_mode", False)

    # Also treat any non-command long message as potential chat if AI is available
    if ai.is_ai_available() and (in_chat_mode or len(text) > 12):
        # Auto-enable chat mode on first free message
        context.user_data["chat_mode"] = True
        await handle_ai_chat(update, context, text)
        return

    # Fallback
    await update.message.reply_text(
        "Samajh nahi aaya.\n\n"
        "Buttons use karo ya /help dekho.\n"
        "AI Coach se baat karni ho to /chat likho ya seedha apna message bhej do.",
        reply_markup=main_keyboard()
    )



# ==================== PREMIUM & SUBSCRIPTION ====================

# Admin user IDs (apna Telegram user ID yahan daalo)
# Apna ID pata karne ke liye bot ko /myid bhejo
ADMIN_IDS = set()
_admin_env = os.getenv("ADMIN_IDS", "")
if _admin_env:
    for x in _admin_env.split(","):
        x = x.strip()
        if x.isdigit():
            ADMIN_IDS.add(int(x))

# Pricing (India friendly)
PLANS = {
    "monthly": {"price": 79, "days": 30, "label": "1 Month - ₹79"},
    "quarterly": {"price": 199, "days": 90, "label": "3 Months - ₹199"},
    "yearly": {"price": 499, "days": 365, "label": "1 Year - ₹499"},
}

# UPI ID for payments (change this)
UPI_ID = os.getenv("UPI_ID", "yourupi@paytm")
UPI_NAME = os.getenv("UPI_NAME", "LoA Bot Premium")


async def premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username, user.first_name)

    is_prem = db.is_premium(user.id)
    until = db.get_premium_until(user.id)

    if is_prem:
        status = f"✅ *Premium Active*\nValid till: `{until}`"
    else:
        status = "🆓 *Free Plan*"

    usage = db.get_usage(user.id)

    text = f"""
💎 *Premium Plans*

{status}

*Free Plan limits (per day):*
• AI Chat: {usage['chat_count']}/{db.FREE_CHAT_LIMIT}
• Affirmations: {usage['affirmation_count']}/{db.FREE_AFFIRMATION_LIMIT}
• Goals: max {db.FREE_GOAL_LIMIT}

*Premium Benefits:*
• ∞ Unlimited AI Chat
• ∞ Unlimited Affirmations
• ∞ Unlimited Goals
• Daily AI Morning Messages
• Longer chat memory
• Priority support

*Plans (India):*
• 1 Month → *₹79*
• 3 Months → *₹199* (best value)
• 1 Year → *₹499*

*Kaise lein:*
1. Neeche UPI pe pay karo
2. Payment screenshot is bot pe bhejo
3. Admin activate kar dega (usually 1-2 hours)

UPI: `{UPI_ID}`
Name: {UPI_NAME}

Payment ke baad screenshot bhej do + plan likh do (monthly/quarterly/yearly)
"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User apna Telegram ID dekh sake (admin setup ke liye)"""
    uid = update.effective_user.id
    await update.message.reply_text(f"Aapka Telegram User ID: `{uid}`", parse_mode=ParseMode.MARKDOWN)


async def addpremium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin only: /addpremium <user_id> <days>"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Ye command sirf admin ke liye hai.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /addpremium <user_id> <days>\nExample: /addpremium 123456789 30")
        return

    try:
        target_id = int(args[0])
        days = int(args[1])
    except ValueError:
        await update.message.reply_text("User ID aur days number hone chahiye.")
        return

    db.ensure_user(target_id)
    db.set_premium(target_id, True, days=days, activated_by=str(user.id), note="manual admin")
    until = db.get_premium_until(target_id)

    await update.message.reply_text(
        f"✅ Premium activate ho gaya!\nUser: `{target_id}`\nDays: {days}\nTill: {until}",
        parse_mode=ParseMode.MARKDOWN
    )

    # Notify the user
    try:
        notify = (
            f"🎉 *Premium Activate Ho Gaya!*\n\n"
            f"Aapka plan {days} din ke liye active hai.\n"
            f"Valid till: {until}\n\n"
            f"Ab unlimited AI chat + saari features use kar sakte ho. Enjoy! 💎"
        )
        await context.bot.send_message(
            chat_id=target_id,
            text=notify,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass


async def removepremium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("Ye command sirf admin ke liye hai.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /removepremium <user_id>")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID")
        return

    db.set_premium(target_id, False)
    await update.message.reply_text(f"Premium hata diya gaya: `{target_id}`", parse_mode=ParseMode.MARKDOWN)



# ==================== DAILY JOB ====================

async def send_daily_messages(context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_daily_users()
    logger.info(f"Sending daily messages to {len(users)} users")

    for u in users:
        try:
            user_id = u["user_id"]
            goals = get_user_goals_texts(user_id)
            name = u["first_name"] or None
            streak = u["streak"] or 0

            message = None
            if ai.is_ai_available():
                message = ai.generate_daily_ai_message(goals, streak, name)

            if not message:
                message = local_get_daily_message(goals, streak, name)

            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send daily to {u['user_id']}: {e}")


# ==================== MAIN ====================

def main():
    if not TOKEN:
        print("=" * 60)
        print("ERROR: TELEGRAM_BOT_TOKEN set nahi hai!")
        print()
        print("1. @BotFather se token lo")
        print("2. export TELEGRAM_BOT_TOKEN='your-token'")
        print("3. (Optional but recommended) export OPENAI_API_KEY='sk-...'")
        print("4. python bot.py")
        print("=" * 60)
        return

    db.init_db()
    logger.info("Database initialized")

    if ai.is_ai_available():
        logger.info(f"AI Coach enabled — {ai.get_provider_info()}")
        print(f"✅ AI Coach ENABLED → {ai.get_provider_info()}")
    else:
        logger.warning("No AI API key found — AI Coach disabled, local mode only")
        print("⚠️  AI key nahi mili — AI Coach OFF (local affirmations chalenge)")
        print("   .env mein GROQ_API_KEY ya OPENAI_API_KEY set karo")

    application = Application.builder().token(TOKEN).build()

    # Conversations
    goal_conv = ConversationHandler(
        entry_points=[CommandHandler("setgoal", setgoal_start)],
        states={
            WAITING_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_goal)],
            WAITING_CATEGORY: [CallbackQueryHandler(receive_category, pattern="^cat_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    gratitude_conv = ConversationHandler(
        entry_points=[
            CommandHandler("gratitude", gratitude_start),
            MessageHandler(filters.Regex("(?i)^🙏?\\s*gratitude"), gratitude_start),
        ],
        states={
            WAITING_GRATITUDE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_gratitude)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("affirmation", affirmation_cmd))
    application.add_handler(CommandHandler("visualize", visualize_cmd))
    application.add_handler(CommandHandler("streak", streak_cmd))
    application.add_handler(CommandHandler("mygoals", mygoals_cmd))
    application.add_handler(CommandHandler("settings", settings_cmd))
    application.add_handler(CommandHandler("daily", daily_cmd))
    application.add_handler(CommandHandler("chat", chat_cmd))
    application.add_handler(CommandHandler("stopchat", stopchat_cmd))
    application.add_handler(CommandHandler("clear", clear_cmd))
    application.add_handler(CommandHandler("premium", premium_cmd))
    application.add_handler(CommandHandler("subscribe", premium_cmd))
    application.add_handler(CommandHandler("myid", myid_cmd))
    application.add_handler(CommandHandler("addpremium", addpremium_cmd))
    application.add_handler(CommandHandler("removepremium", removepremium_cmd))

    application.add_handler(goal_conv)
    application.add_handler(gratitude_conv)

    application.add_handler(CallbackQueryHandler(daily_callback, pattern="^daily_"))
    application.add_handler(CallbackQueryHandler(goals_callback, pattern="^(add_goal|list_goals|remove_goal|delgoal_)"))

    # General text (must be last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Daily job
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_daily(
            send_daily_messages,
            time=time(hour=8, minute=0),
            name="daily_loa"
        )
        logger.info("Daily job scheduled for 08:00")

    logger.info("Bot starting...")
    print("✅ Law of Attraction Bot + AI Coach is running!")
    print("Telegram pe /start bhejo.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
