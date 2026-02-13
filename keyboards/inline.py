"""
Supreme Hosting Bot - Inline Keyboards
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import PUBLIC_CHANNEL, PRIVATE_CHANNEL, OWNER_USERNAME


class Keyboards:

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📤 Upload Bot", callback_data="upload"),
            InlineKeyboardButton(text="🤖 My Bots", callback_data="mybots")
        )
        builder.row(
            InlineKeyboardButton(text="👤 Profile", callback_data="profile"),
            InlineKeyboardButton(text="📖 Help", callback_data="help")
        )
        builder.row(
            InlineKeyboardButton(text="📢 Channel", url=PUBLIC_CHANNEL),
            InlineKeyboardButton(text="🔐 VIP Channel", url=PRIVATE_CHANNEL)
        )
        builder.row(
            InlineKeyboardButton(text="👨‍💻 Developer", url=f"https://t.me/shuvohassan00")
        )
        return builder.as_markup()

    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔙 Back to Menu", callback_data="start")
        )
        return builder.as_markup()

    @staticmethod
    def bot_management(bot_id: int, status: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        if status == "running":
            builder.row(
                InlineKeyboardButton(text="⏹️ Stop", callback_data=f"stop_{bot_id}"),
                InlineKeyboardButton(text="🔄 Restart", callback_data=f"restart_{bot_id}")
            )
        else:
            builder.row(
                InlineKeyboardButton(text="▶️ Start", callback_data=f"start_{bot_id}")
            )
        
        builder.row(
            InlineKeyboardButton(text="📋 Logs", callback_data=f"logs_{bot_id}"),
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"delete_{bot_id}")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Back to My Bots", callback_data="mybots")
        )
        return builder.as_markup()

    @staticmethod
    def confirm_delete(bot_id: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Yes, Delete", callback_data=f"confirmdelete_{bot_id}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"manage_{bot_id}")
        )
        return builder.as_markup()

    @staticmethod
    def bot_list(bots: list) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for bot in bots:
            status_emoji = "🟢" if bot['status'] == 'running' else "🔴"
            builder.row(
                InlineKeyboardButton(
                    text=f"{status_emoji} #{bot['bot_id']} — {bot['original_name'][:25]}",
                    callback_data=f"manage_{bot['bot_id']}"
                )
            )
        builder.row(
            InlineKeyboardButton(text="📤 Upload New Bot", callback_data="upload"),
            InlineKeyboardButton(text="🔙 Menu", callback_data="start")
        )
        return builder.as_markup()

    @staticmethod
    def logs_keyboard(bot_id: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 Refresh", callback_data=f"logs_{bot_id}"),
            InlineKeyboardButton(text="🗑️ Clear Logs", callback_data=f"clearlogs_{bot_id}")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Back", callback_data=f"manage_{bot_id}")
        )
        return builder.as_markup()

    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📊 Statistics", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Users", callback_data="admin_users")
        )
        builder.row(
            InlineKeyboardButton(text="👑 Premium Users", callback_data="admin_premium"),
            InlineKeyboardButton(text="🤖 All Bots", callback_data="admin_allbots")
        )
        builder.row(
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast"),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Menu", callback_data="start")
        )
        return builder.as_markup()

    @staticmethod
    def owner_panel() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📊 Statistics", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 All Users", callback_data="admin_users")
        )
        builder.row(
            InlineKeyboardButton(text="👑 Premium Users", callback_data="admin_premium"),
            InlineKeyboardButton(text="🛡️ Admins", callback_data="owner_admins")
        )
        builder.row(
            InlineKeyboardButton(text="🤖 All Bots", callback_data="admin_allbots"),
            InlineKeyboardButton(text="🛑 Kill All", callback_data="owner_killall")
        )
        builder.row(
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast"),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Menu", callback_data="start")
        )
        return builder.as_markup()
