"""
Supreme Hosting Bot - Authentication Middleware
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from database import db
from config import OWNER_ID


class AuthMiddleware(BaseMiddleware):
    """
    Middleware that:
    1. Registers users automatically
    2. Checks if user is banned
    3. Injects user data into handler
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        user = None
        
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user:
            # Auto-register user
            username = user.username or ""
            full_name = user.full_name or "Unknown"
            await db.create_user(user.id, username, full_name)
            
            # Fetch user data
            db_user = await db.get_user(user.id)
            data["db_user"] = db_user
            
            # Check ban (owner is never banned)
            if db_user and db_user.get('is_banned') and user.id != OWNER_ID:
                from utils.texts import Texts
                if isinstance(event, Message):
                    await event.answer(Texts.banned_msg(), parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 You are banned!", show_alert=True)
                return

        return await handler(event, data)
