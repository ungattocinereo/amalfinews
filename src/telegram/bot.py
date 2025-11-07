"""
Telegram bot for event moderation
"""

import logging
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from src.core.database import get_database
from src.core.models import EventStatus
from src.telegram.keyboards import create_event_keyboard
from src.telegram.handlers import (
    start_command, events_command, stats_command,
    sources_command, help_command, button_callback
)


logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram moderation bot"""

    def __init__(self, token: str, admin_id: str):
        self.token = token
        self.admin_id = admin_id
        self.application = None

    def setup(self):
        """Setup bot with handlers"""
        self.application = Application.builder().token(self.token).build()

        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("events", events_command))
        self.application.add_handler(CommandHandler("stats", stats_command))
        self.application.add_handler(CommandHandler("sources", sources_command))
        self.application.add_handler(CommandHandler("help", help_command))

        # Callback handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(button_callback))

        logger.info("Telegram bot setup complete")

    async def start(self):
        """Start bot polling"""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Telegram bot started")

    async def stop(self):
        """Stop bot"""
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("Telegram bot stopped")

    async def send_message(self, text: str, parse_mode: str = "Markdown"):
        """Send message to admin"""
        try:
            await self.application.bot.send_message(
                chat_id=self.admin_id,
                text=text,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def send_event_for_review(self, event_id: int):
        """Send event to admin for review"""
        db = get_database()
        event = db.get_processed_event(event_id)

        if not event:
            logger.error(f"Event {event_id} not found")
            return

        # Format message
        message = self._format_event_message(event)

        # Create keyboard
        keyboard = create_event_keyboard(event_id)

        try:
            await self.application.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            logger.info(f"Event {event_id} sent for review")
        except Exception as e:
            logger.error(f"Failed to send event {event_id}: {e}")

    def _format_event_message(self, event) -> str:
        """Format event as Telegram message"""
        date_str = event.event_date.strftime('%B %d, %Y')

        message = f"""🎯 *Event #{event.id} for Review*

📅 *Date:* {date_str}
📍 *Location:* {event.location}

*{event.title_en}*

{event.description_en}

"""
        if event.price_info:
            message += f"💰 *Price:* {event.price_info}\n"

        if event.accessibility:
            message += f"🚌 *How to get there:* {event.accessibility}\n"

        if event.keywords:
            tags = " ".join([f"#{k.replace(' ', '_')}" for k in event.keywords[:3]])
            message += f"\n{tags}\n"

        return message
