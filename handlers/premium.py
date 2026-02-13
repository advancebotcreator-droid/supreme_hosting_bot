"""
Supreme Hosting Bot - Premium Management Handlers
"""

import re
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command

from utils.texts import Texts
from database import db
from config import OWNER_ID

router = Router()


def is_admin_or_owner(user_id: int, db_user: dict = None) -> bool:
    if user_id == OWNER_ID:
        return True
    if db_user and db_user.get('is_admin'):
        return True
    return False


@router.message(Command("addpremium"))
async def cmd_add_premium(message: Message, bot: Bot, db_user: dict = None):
    """
    Usage: /addpremium @user 30d
           /addpremium user_id 7d
           /addpremium (reply) 30d
    """
    if not is_admin_or_owner(message.from_user.id, db_user):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    args = message.text.split()
    
    # Parse duration and target
    target_id = None
    duration_str = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        if len(args) >= 2:
            duration_str = args[1]
    elif len(args) >= 3:
        # /addpremium @user 30d
        target = args[1]
        duration_str = args[2]
        
        if target.isdigit():
            target_id = int(target)
        else:
            username = target.lstrip("@")
            all_users = await db.get_all_users()
            for u in all_users:
                if u.get('username', '').lower() == username.lower():
                    target_id = u['user_id']
                    break
    
    if not target_id or not duration_str:
        await message.reply(
            "❌ <b>Usage:</b>\n"
            "<code>/addpremium @username 30d</code>\n"
            "<code>/addpremium user_id 7d</code>\n"
            "<code>/addpremium 15d</code> (reply to user)\n\n"
            "<b>Duration examples:</b> 1d, 7d, 30d, 365d",
            parse_mode="HTML"
        )
        return

    # Parse duration
    match = re.match(r'^(\d+)([dD])$', duration_str)
    if not match:
        await message.reply(
            "❌ <b>Invalid duration!</b>\n\n"
            "Use format: <code>30d</code> (for 30 days)\n"
            "Examples: 1d, 7d, 30d, 90d, 365d",
            parse_mode="HTML"
        )
        return

    days = int(match.group(1))
    if days <= 0 or days > 3650:
        await message.reply("❌ Duration must be between 1 and 3650 days!", parse_mode="HTML")
        return

    # Check if target exists
    target_user = await db.get_user(target_id)
    if not target_user:
        await message.reply("❌ User not found! They must start the bot first.", parse_mode="HTML")
        return

    # Grant premium
    await db.set_premium(target_id, days)
    await db.log_activity(
        message.from_user.id, "add_premium",
        f"Granted {days}d premium to {target_id}"
    )

    await message.reply(
        f"✅ <b>Premium Granted!</b>\n\n"
        f"👤 {target_user['full_name']}\n"
        f"🆔 <code>{target_id}</code>\n"
        f"⏳ Duration: <b>{days} days</b>",
        parse_mode="HTML"
    )

    # Notify the user
    try:
        await bot.send_message(
            target_id,
            Texts.premium_granted(days, message.from_user.full_name),
            parse_mode="HTML"
        )
    except Exception:
        pass

    # Notify admin group
    admin_group = await db.get_admin_group()
    if admin_group:
        try:
            await bot.send_message(
                admin_group,
                f"👑 <b>Premium Granted!</b>\n\n"
                f"👤 {target_user['full_name']} (<code>{target_id}</code>)\n"
                f"⏳ {days} days\n"
                f"By: {message.from_user.full_name}",
                parse_mode="HTML"
            )
        except:
            pass


@router.message(Command("removepremium"))
async def cmd_remove_premium(message: Message, bot: Bot, db_user: dict = None):
    if not is_admin_or_owner(message.from_user.id, db_user):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    target_id = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    else:
        args = message.text.split()
        if len(args) >= 2:
            target = args[1]
            if target.isdigit():
                target_id = int(target)
            else:
                username = target.lstrip("@")
                all_users = await db.get_all_users()
                for u in all_users:
                    if u.get('username', '').lower() == username.lower():
                        target_id = u['user_id']
                        break

    if not target_id:
        await message.reply(
            "❌ <b>Usage:</b> <code>/removepremium @user</code> or reply to user",
            parse_mode="HTML"
        )
        return

    target_user = await db.get_user(target_id)
    if not target_user:
        await message.reply("❌ User not found!", parse_mode="HTML")
        return

    await db.revoke_premium(target_id)
    await db.log_activity(
        message.from_user.id, "remove_premium", f"Revoked premium from {target_id}"
    )

    await message.reply(
        f"✅ <b>Premium Revoked!</b>\n\n"
        f"👤 {target_user['full_name']}\n"
        f"🆔 <code>{target_id}</code>",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            target_id,
            Texts.premium_expired(),
            parse_mode="HTML"
        )
    except:
        pass
