"""
Telegram inline keyboards
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def create_event_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """Create inline keyboard for event review"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{event_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{event_id}")
        ],
        [
            InlineKeyboardButton("⏭️ Skip", callback_data=f"skip_{event_id}")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)
