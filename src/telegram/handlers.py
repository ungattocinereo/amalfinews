"""
Telegram command handlers
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from src.core.database import get_database
from src.core.models import EventStatus
from src.telegram.keyboards import create_event_keyboard


logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "🎯 *Amalfi Events Moderation Bot*\n\n"
        "Commands:\n"
        "/events - Show pending events\n"
        "/stats - View statistics\n"
        "/sources - Check source health\n"
        "/help - Show help",
        parse_mode="Markdown"
    )


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /events command - show pending events"""
    db = get_database()
    pending = db.get_pending_events(limit=5)

    if not pending:
        await update.message.reply_text("No pending events for review.")
        return

    await update.message.reply_text(
        f"📋 *{len(pending)} Pending Events*\n\n"
        "Sending events for review...",
        parse_mode="Markdown"
    )

    # Send each event
    for event in pending:
        message = _format_event_message(event)
        keyboard = create_event_keyboard(event.id)

        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    db = get_database()
    stats = db.get_daily_stats()

    message = f"""📊 *Daily Statistics*

🕷️ Events Scraped: {stats['scraped']}
🌍 Events Translated: {stats['translated']}
⏳ Pending Review: {stats['pending']}
✅ Approved: {stats['approved']}
❌ Rejected: {stats['rejected']}
📝 Published: {stats['published']}

📅 Date: {datetime.now().strftime('%Y-%m-%d')}
"""

    await update.message.reply_text(message, parse_mode="Markdown")


async def sources_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sources command"""
    await update.message.reply_text(
        "🌐 *News Sources*\n\n"
        "Run health check to see source status.\n"
        "Use `python scripts/test_sources.py`",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """🆘 *Help - Amalfi Events Bot*

*Commands:*
/events - Show pending events for review (max 5)
/stats - View daily processing statistics
/sources - Check news source health
/help - Show this help message

*Reviewing Events:*
• Click ✅ Approve to publish event
• Click ❌ Reject to discard event
• Click ⏭️ Skip to review later

*Event Information:*
Each event shows:
• Date and location
• English description
• Price and accessibility info
• Keywords/tags

Questions? Check the documentation.
"""

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()

    data = query.data
    action, event_id_str = data.split('_', 1)
    event_id = int(event_id_str)

    db = get_database()
    event = db.get_processed_event(event_id)

    if not event:
        await query.edit_message_text("❌ Event not found")
        return

    user_id = str(update.effective_user.id)

    if action == "approve":
        db.update_event_status(event_id, EventStatus.APPROVED, moderated_by=user_id)
        await query.edit_message_text(
            f"✅ *Event Approved*\n\n{event.title_en}\n\n"
            "Event will be published to WordPress.",
            parse_mode="Markdown"
        )
        logger.info(f"Event {event_id} approved by {user_id}")

    elif action == "reject":
        db.update_event_status(event_id, EventStatus.REJECTED, moderated_by=user_id)
        await query.edit_message_text(
            f"❌ *Event Rejected*\n\n{event.title_en}",
            parse_mode="Markdown"
        )
        logger.info(f"Event {event_id} rejected by {user_id}")

    elif action == "skip":
        await query.edit_message_text(
            f"⏭️ *Skipped*\n\n{event.title_en}\n\nUse /events to review later.",
            parse_mode="Markdown"
        )


def _format_event_message(event) -> str:
    """Format event for display"""
    date_str = event.event_date.strftime('%B %d, %Y')

    message = f"""🎯 *Event #{event.id}*

📅 {date_str}
📍 {event.location}

*{event.title_en}*

{event.description_en[:300]}{'...' if len(event.description_en) > 300 else ''}
"""

    return message
