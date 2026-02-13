"""
Supreme Hosting Bot - Admin Panel Handlers
"""

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from utils.texts import Texts
from keyboards.inline import Keyboards
from database import db
from config import OWNER_ID
from services.process_manager import process_manager

router = Router()


def is_admin_or_owner(user_id: int, db_user: dict = None) -> bool:
    if user_id == OWNER_ID:
        return True
    if db_user and db_user.get('is_admin'):
        return True
    return False


@router.message(Command("stats"))
async def cmd_stats(message: Message, db_user: dict = None):
    if not is_admin_or_owner(message.from_user.id, db_user):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return
    
    total_users = await db.get_user_count()
    premium_users = len(await db.get_premium_users())
    admins = len(await db.get_all_admins())
    total_bots = await db.get_total_bots()
    running_bots = process_manager.get_running_count()

    await message.reply(
        Texts.stats(total_users, premium_users, admins, total_bots, running_bots),
        parse_mode="HTML",
        reply_markup=Keyboards.back_to_menu()
    )


@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery, db_user: dict = None):
    if not is_admin_or_owner(callback.from_user.id, db_user):
        await callback.answer("🔒 Unauthorized!", show_alert=True)
        return

    total_users = await db.get_user_count()
    premium_users = len(await db.get_premium_users())
    admins = len(await db.get_all_admins())
    total_bots = await db.get_total_bots()
    running_bots = process_manager.get_running_count()

    kb = Keyboards.owner_panel() if callback.from_user.id == OWNER_ID else Keyboards.admin_panel()
    
    await callback.message.edit_text(
        Texts.stats(total_users, premium_users, admins, total_bots, running_bots),
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: CallbackQuery, db_user: dict = None):
    if not is_admin_or_owner(callback.from_user.id, db_user):
        await callback.answer("🔒 Unauthorized!", show_alert=True)
        return

    users = await db.get_all_users()
    text = (
        f"╔══════════════════════════╗\n"
        f"   👥 <b>All Users</b> ({len(users)})\n"
        f"╚══════════════════════════╝\n\n"
    )
    
    for u in users[:50]:  # Limit to 50
        premium = "👑" if u['is_premium'] else "🆓"
        admin = "🛡️" if u['is_admin'] else ""
        banned = "🚫" if u['is_banned'] else ""
        text += f"{premium}{admin}{banned} <code>{u['user_id']}</code> — {u['full_name'][:20]}\n"
    
    if len(users) > 50:
        text += f"\n<i>... and {len(users) - 50} more</i>"

    kb = Keyboards.owner_panel() if callback.from_user.id == OWNER_ID else Keyboards.admin_panel()
    
    if len(text) > 4000:
        text = text[:3950] + "\n\n<i>... truncated</i>"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin_premium")
async def cb_admin_premium(callback: CallbackQuery, db_user: dict = None):
    if not is_admin_or_owner(callback.from_user.id, db_user):
        await callback.answer("🔒 Unauthorized!", show_alert=True)
        return

    from datetime import datetime

    users = await db.get_premium_users()
    text = (
        f"╔══════════════════════════╗\n"
        f"   👑 <b>Premium Users</b> ({len(users)})\n"
        f"╚══════════════════════════╝\n\n"
    )
    
    if not users:
        text += "<i>No premium users yet.</i>"
    else:
        for u in users:
            exp = datetime.fromtimestamp(u['premium_expires_at']).strftime("%Y-%m-%d") if u['premium_expires_at'] > 0 else "N/A"
            text += f"👑 <code>{u['user_id']}</code> — {u['full_name'][:20]} (exp: {exp})\n"

    kb = Keyboards.owner_panel() if callback.from_user.id == OWNER_ID else Keyboards.admin_panel()
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin_allbots")
async def cb_admin_allbots(callback: CallbackQuery, db_user: dict = None):
    if not is_admin_or_owner(callback.from_user.id, db_user):
        await callback.answer("🔒 Unauthorized!", show_alert=True)
        return

    # Get all bots from all users
    all_users = await db.get_all_users()
    text = (
        f"╔══════════════════════════╗\n"
        f"   🤖 <b>All Hosted Bots</b>\n"
        f"╚══════════════════════════╝\n\n"
    )
    
    total = 0
    for u in all_users:
        bots = await db.get_user_bots(u['user_id'])
        if bots:
            text += f"👤 <b>{u['full_name'][:20]}</b> (<code>{u['user_id']}</code>):\n"
            for b in bots:
                status = "🟢" if b['status'] == 'running' else "🔴"
                text += f"  {status} #{b['bot_id']} — {b['original_name'][:20]}\n"
                total += 1
            text += "\n"

    if total == 0:
        text += "<i>No bots deployed yet.</i>"
    else:
        text += f"━━━━━━━━━━━━━━━━━━━━━━\n<b>Total: {total} bots</b>"

    kb = Keyboards.owner_panel() if callback.from_user.id == OWNER_ID else Keyboards.admin_panel()
    
    if len(text) > 4000:
        text = text[:3950] + "\n\n<i>... truncated</i>"
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.message(Command("ban"))
async def cmd_ban(message: Message, bot: Bot, db_user: dict = None):
    if not is_admin_or_owner(message.from_user.id, db_user):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    target_id = await _resolve_user_id(message, bot)
    if not target_id:
        return

    if target_id == OWNER_ID:
        await message.reply("❌ Cannot ban the owner!", parse_mode="HTML")
        return

    await db.set_banned(target_id, True)
    await db.log_activity(message.from_user.id, "ban_user", f"Banned {target_id}")
    
    await message.reply(
        f"🚫 <b>User Banned!</b>\n\nUser <code>{target_id}</code> has been banned.",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            target_id,
            "🚫 <b>You have been banned</b> from using this bot.\n"
            f"Contact {Texts.OWNER_USERNAME if hasattr(Texts, 'OWNER_USERNAME') else '@shuvohassan00'} for appeal.",
            parse_mode="HTML"
        )
    except:
        pass


@router.message(Command("unban"))
async def cmd_unban(message: Message, bot: Bot, db_user: dict = None):
    if not is_admin_or_owner(message.from_user.id, db_user):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    target_id = await _resolve_user_id(message, bot)
    if not target_id:
        return

    await db.set_banned(target_id, False)
    await db.log_activity(message.from_user.id, "unban_user", f"Unbanned {target_id}")
    
    await message.reply(
        f"✅ <b>User Unbanned!</b>\n\nUser <code>{target_id}</code> has been unbanned.",
        parse_mode="HTML"
    )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, bot: Bot, db_user: dict = None):
    if not is_admin_or_owner(message.from_user.id, db_user):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    text = message.text.replace("/broadcast", "", 1).strip()
    if not text:
        await message.reply(
            "📢 <b>Usage:</b> <code>/broadcast Your message here</code>",
            parse_mode="HTML"
        )
        return

    broadcast_text = (
        f"╔══════════════════════════╗\n"
        f"   📢 <b>ANNOUNCEMENT</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>From {BOT_NAME} Team</i>"
    )

    users = await db.get_all_users()
    success = 0
    failed = 0

    from config import BOT_NAME

    status_msg = await message.reply(
        f"📢 <b>Broadcasting to {len(users)} users...</b>",
        parse_mode="HTML"
    )

    for user in users:
        try:
            await bot.send_message(
                user['user_id'],
                broadcast_text,
                parse_mode="HTML"
            )
            success += 1
        except Exception:
            failed += 1

        # Avoid flood
        if (success + failed) % 25 == 0:
            import asyncio
            await asyncio.sleep(1)

    await status_msg.edit_text(
        f"📢 <b>Broadcast Complete!</b>\n\n"
        f"✅ <b>Sent:</b> {success}\n"
        f"❌ <b>Failed:</b> {failed}\n"
        f"📊 <b>Total:</b> {len(users)}",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, db_user: dict = None):
    if not is_admin_or_owner(callback.from_user.id, db_user):
        await callback.answer("🔒 Unauthorized!", show_alert=True)
        return

    await callback.message.edit_text(
        "📢 <b>Broadcast Message</b>\n\n"
        "Send the command:\n<code>/broadcast Your message here</code>\n\n"
        "<i>The message will be sent to all users.</i>",
        parse_mode="HTML",
        reply_markup=Keyboards.back_to_menu()
    )
    await callback.answer()


async def _resolve_user_id(message: Message, bot: Bot) -> int:
    """Resolve user ID from command arguments (supports reply, @username, or ID)."""
    # Check reply
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id

    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "❌ <b>Usage:</b> Reply to a user's message or provide user ID\n"
            "<code>/command user_id</code>",
            parse_mode="HTML"
        )
        return None

    target = args[1]
    
    # Direct ID
    if target.isdigit():
        return int(target)

    # Username - look up in database
    username = target.lstrip("@")
    all_users = await db.get_all_users()
    for u in all_users:
        if u.get('username', '').lower() == username.lower():
            return u['user_id']

    await message.reply(
        f"❌ User <code>{target}</code> not found in database.\n"
        f"<i>User must have started the bot first, or use their numeric ID.</i>",
        parse_mode="HTML"
    )
    return None
