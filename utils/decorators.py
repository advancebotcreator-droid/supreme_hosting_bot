from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from database import db

def owner_only(func):
    """Decorator to restrict command to owner only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID:
            await update.message.reply_text(
                f"{Config.EMOJI['cross']} **Access Denied!**\n\n"
                f"This command is only available to the bot owner.",
                parse_mode='Markdown'
            )
            return
        return await func(update, context)
    return wrapper

def admin_only(func):
    """Decorator to restrict command to admins only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != Config.OWNER_ID and not db.is_admin(user_id):
            await update.message.reply_text(
                f"{Config.EMOJI['cross']} **Access Denied!**\n\n"
                f"This command is only available to administrators.",
                parse_mode='Markdown'
            )
            return
        return await func(update, context)
    return wrapper

def check_banned(func):
    """Check if user is banned"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if db.is_banned(user_id):
            await update.message.reply_text(
                f"{Config.EMOJI['cross']} **You are banned!**\n\n"
                f"You cannot use this bot. Contact the owner if you think this is a mistake.",
                parse_mode='Markdown'
            )
            return
        return await func(update, context)
    return wrapper

def track_user(func):
    """Track user activity"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db.add_user(user.id, user.username, user.first_name, user.last_name)
        return await func(update, context)
    return wrapper
