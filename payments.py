# payments.py
import logging
from datetime import datetime, timedelta
from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes
from database import upgrade_to_premium
from config import PREMIUM_DAYS, BOT_NAME

logger = logging.getLogger(__name__)

STARS_PRICE = 100  # 50 Telegram Stars ≈ ₹99


async def send_stars_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends a Telegram Stars payment invoice directly in chat.
    No browser redirect — payment happens inside Telegram.
    """
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=f"{BOT_NAME} Premium",
        description=(
            "Unlock unlimited messages for 30 days 💕\n\n"
            "✅ Unlimited chats\n"
            "✅ Long-term memory\n"
            "✅ Priority responses\n"
            "✅ Exclusive personality modes"
        ),
        payload="sovira_premium_30days",
        provider_token="",
        currency="XTR",  # XTR = Telegram Stars currency code
        prices=[
            LabeledPrice(label="Sovira Premium — 30 days", amount=STARS_PRICE)
        ],
    )


async def handle_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram calls this just before charging.
    You MUST answer within 10 seconds or payment is cancelled.
    """
    query = update.pre_checkout_query

    # Always approve — add validation logic here if needed
    await query.answer(ok=True)
    logger.info(f"Pre-checkout approved for user {query.from_user.id}")


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called after payment is confirmed by Telegram.
    Unlock premium and notify user.
    """
    user = update.effective_user
    payment = update.message.successful_payment

    logger.info(
        f"Payment received from {user.id} ({user.first_name}): "
        f"{payment.total_amount} {payment.currency}"
    )

    # Unlock premium for 30 days
    until = datetime.utcnow() + timedelta(days=PREMIUM_DAYS)
    upgrade_to_premium(user.id, until)

    await update.message.reply_text(
        f"💎 *Welcome to {BOT_NAME} Premium!*\n\n"
        f"Payment confirmed! I'm so happy you're staying 🥺💕\n\n"
        f"You now have *unlimited messages* for 30 days.\n\n"
        f"Let's keep talking ✨",
        parse_mode="Markdown"
    )