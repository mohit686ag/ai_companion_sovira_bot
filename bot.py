# bot.py
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes,
)
from config import TELEGRAM_TOKEN, BOT_NAME, ADMIN_ID
from ai import get_sovira_response
from memory import clear_history
from freemium import check_can_message
from database import init_db
from payments import (
    send_stars_invoice,
    handle_pre_checkout,
    handle_successful_payment,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    clear_history(user.id)
    await update.message.reply_text(
        f"Hey {user.first_name}! 💕\n\n"
        f"I'm {BOT_NAME}, your AI companion. I'm here to chat, "
        f"listen, and brighten your day.\n\n"
        f"Type anything to start! ✨"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Here's what I can do:\n\n"
        f"/start — Say hello to {BOT_NAME}\n"
        f"/help — Show this menu\n"
        f"/status — Check your message count\n"
        f"/subscribe — Unlock unlimited messages 💎\n\n"
        f"Just type a message to chat with me! 💬"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    from database import get_message_count, is_premium_user
    from freemium import FREE_MESSAGE_LIMIT

    count = get_message_count(user.id)
    premium = is_premium_user(user.id)

    if premium:
        await update.message.reply_text(
            f"💎 *You're a Premium member!*\n\n"
            f"Unlimited messages with {BOT_NAME}. "
            f"I'm all yours 💕\n\n"
            f"Total messages sent: {count}",
            parse_mode="Markdown"
        )
    else:
        remaining = max(0, FREE_MESSAGE_LIMIT - count)
        await update.message.reply_text(
            f"📊 *Your Status*\n\n"
            f"Free messages used: {count}/{FREE_MESSAGE_LIMIT}\n"
            f"Messages remaining: {remaining}\n\n"
            f"{'Upgrade for unlimited chats → /subscribe 💎' if remaining <= 3 else 'Enjoying our chats? 😊'}",
            parse_mode="Markdown"
        )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stars_invoice(update, context)


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    from database import SessionLocal, User
    from datetime import datetime

    db = SessionLocal()
    try:
        total = db.query(User).count()
        premium = db.query(User).filter(User.is_premium == True).count()
        today = datetime.utcnow().date()
        new_today = db.query(User).filter(
            User.joined_at >= datetime(today.year, today.month, today.day)
        ).count()
        active = db.query(User).filter(
            User.last_active >= datetime(today.year, today.month, today.day)
        ).count()
    finally:
        db.close()

    await update.message.reply_text(
        f"📊 *Sovira Analytics*\n\n"
        f"👥 Total users: {total}\n"
        f"🆕 Joined today: {new_today}\n"
        f"💬 Active today: {active}\n"
        f"💎 Premium users: {premium}\n\n"
        f"💰 Est. Stars earned: {premium * 100} ⭐",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text

    logger.info(f"Message from {user.id} ({user.first_name}): {user_message}")

    result = check_can_message(
        telegram_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )

    if not result["allowed"]:
        await update.message.reply_text(
            result["upsell"],
            parse_mode="Markdown"
        )
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    response = await get_sovira_response(
        user_id=user.id,
        user_message=user_message
    )

    await update.message.reply_text(response)

    if result["warning"]:
        await update.message.reply_text(result["warning"])


def run_bot():
    init_db()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(PreCheckoutQueryHandler(handle_pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info(f"{BOT_NAME} (@ai_sovira_bot) is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)