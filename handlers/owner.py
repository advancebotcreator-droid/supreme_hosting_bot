"""
Supreme Hosting Bot - Owner-Only Handlers
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


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


@router.message(Command("addadmin"))
async def cmd_add_admin(message: Message, bot: Bot, db_user: dict = None):
    if not is_owner(message.from_user.id):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    target_id = await _resolve_user(message, bot)
    if not target_id:
        return

    target_user = await db.get_user(target_id)
    if not target_user:
        await message.reply("❌ User not found! They must start the bot first.", parse_mode="HTML")
        return

    if target_user.get('is_admin'):
        await message.reply("⚠️ User is already an admin!", parse_mode="HTML")
        return

    await db.set_admin(target_id, True)
    await db.log_activity(message.from_user.id, "add_admin", f"Added admin: {target_id}")

    await message.reply(
        f"✅ <b>Admin Added!</b>\n\n"
        f"👤 {target_user['full_name']}\n"
        f"🆔 <code>{target_id}</code>",
        parse_mode="HTML"
    )

    # Notify the new admin
    try:
        await bot.send_message(
            target_id,
            Texts.admin_granted(message.from_user.full_name),
            parse_mode="HTML"
        )
    except:
        pass

    # Notify admin group
    admin_group = await db.get_admin_group()
    if admin_group:
        try:
            await bot.send_message(
                admin_group,
                f"🛡️ <b>New Admin Added!</b>\n\n"
                f"👤 {target_user['full_name']} (<code>{target_id}</code>)\n"
                f"By: {message.from_user.full_name}",
                parse_mode="HTML"
            )
        except:
            pass


@router.message(Command("removeadmin"))
async def cmd_remove_admin(message: Message, bot: Bot, db_user: dict = None):
    if not is_owner(message.from_user.id):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    target_id = await _resolve_user(message, bot)
    if not target_id:
        return

    target_user = await db.get_user(target_id)
    if not target_user:
        await message.reply("❌ User not found!", parse_mode="HTML")
        return

    if not target_user.get('is_admin'):
        await message.reply("⚠️ User is not an admin!", parse_mode="HTML")
        return

    await db.set_admin(target_id, False)
    await db.log_activity(message.from_user.id, "remove_admin", f"Removed admin: {target_id}")

    await message.reply(
        f"✅ <b>Admin Removed!</b>\n\n"
        f"👤 {target_user['full_name']}\n"
        f"🆔 <code>{target_id}</code>",
        parse_mode="HTML"
    )

    # Notify the removed admin
    try:
        await bot.send_message(
            target_id,
            Texts.admin_removed(),
            parse_mode="HTML"
        )
    except:
        pass

    # Notify admin group
    admin_group = await db.get_admin_group()
    if admin_group:
        try:
            await bot.send_message(
                admin_group,
                f"⚠️ <b>Admin Removed!</b>\n\n"
                f"👤 {target_user['full_name']} (<code>{target_id}</code>)\n"
                f"By: {message.from_user.full_name}",
                parse_mode="HTML"
            )
        except:
            pass


@router.message(Command("setgroup"))
async def cmd_set_group(message: Message, db_user: dict = None):
    if not is_owner(message.from_user.id):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    if message.chat.type in ["group", "supergroup"]:
        await db.set_admin_group(message.chat.id)
        await message.reply(
            f"✅ <b>Admin Group Set!</b>\n\n"
            f"Group ID: <code>{message.chat.id}</code>\n"
            f"Group: {message.chat.title}",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            "❌ This command must be used in a group chat!\n\n"
            "Add me to your admin group and send /setgroup there.",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "owner_admins")
async def cb_owner_admins(callback: CallbackQuery, db_user: dict = None):
    if not is_owner(callback.from_user.id):
        await callback.answer("🔒 Owner only!", show_alert=True)
        return

    admins = await db.get_all_admins()
    text = (
        f"╔══════════════════════════╗\n"
        f"   🛡️ <b>Admin List</b> ({len(admins)})\n"
        f"╚══════════════════════════╝\n\n"
    )

    if not admins:
        text += "<i>No admins added yet.</i>\n\nUse <code>/addadmin user_id</code>"
    else:
        for a in admins:
            text += f"🛡️ <code>{a['user_id']}</code> — {a['full_name'][:25]}\n"

    text += (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>/addadmin user_id</code>\n"
        f"<code>/removeadmin user_id</code>"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=Keyboards.owner_panel()
    )
    await callback.answer()


@router.callback_query(F.data == "owner_killall")
async def cb_owner_killall(callback: CallbackQuery, db_user: dict = None):
    if not is_owner(callback.from_user.id):
        await callback.answer("🔒 Owner only!", show_alert=True)
        return

    count = await process_manager.stop_all()
    
    # Update all in database
    running_bots = await db.get_all_running_bots()
    for b in running_bots:
        await db.update_bot_status(b['bot_id'], 'stopped')

    await callback.message.edit_text(
        f"🛑 <b>All Processes Killed!</b>\n\n"
        f"Stopped <b>{count}</b> running process(es).\n"
        f"Database updated.",
        parse_mode="HTML",
        reply_markup=Keyboards.owner_panel()
    )
    await callback.answer("🛑 All killed!", show_alert=True)


@router.message(Command("killall"))
async def cmd_killall(message: Message, db_user: dict = None):
    if not is_owner(message.from_user.id):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    count = await process_manager.stop_all()
    running_bots = await db.get_all_running_bots()
    for b in running_bots:
        await db.update_bot_status(b['bot_id'], 'stopped')

    await message.reply(
        f"🛑 <b>All Processes Killed!</b>\n\nStopped <b>{count}</b> process(es).",
        parse_mode="HTML"
    )


@router.message(Command("allusers"))
async def cmd_all_users(message: Message, db_user: dict = None):
    if not is_owner(message.from_user.id):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    users = await db.get_all_users()
    text = f"👥 <b>All Users ({len(users)}):</b>\n\n"
    
    for u in users[:100]:
        flags = ""
        if u['is_premium']:
            flags += "👑"
        if u['is_admin']:
            flags += "🛡️"
        if u['is_banned']:
            flags += "🚫"
        username = f"@{u['username']}" if u.get('username') else "N/A"
        text += f"{flags} <code>{u['user_id']}</code> — {u['full_name'][:20]} ({username})\n"

    if len(users) > 100:
        text += f"\n<i>Showing 100/{len(users)}</i>"

    if len(text) > 4000:
        text = text[:3950] + "\n...</i>"

    await message.reply(text, parse_mode="HTML")


@router.message(Command("allbots"))
async def cmd_all_bots(message: Message, db_user: dict = None):
    if not is_owner(message.from_user.id):
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    users = await db.get_all_users()
    text = f"🤖 <b>All Hosted Bots:</b>\n\n"
    total = 0

    for u in users:
        bots = await db.get_user_bots(u['user_id'])
        if bots:
            text += f"👤 <b>{u['full_name'][:20]}</b>:\n"
            for b in bots:
                status = "🟢" if b['status'] == 'running' else "🔴"
                text += f"  {status} #{b['bot_id']} — {b['original_name'][:25]}\n"
                total += 1
            text += "\n"

    text += f"━━━━━━━━━━━━━━━━━━━━━━\n<b>Total: {total} bots</b>"

    if len(text) > 4000:
        text = text[:3950] + "\n\n<i>... truncated</i>"

    await message.reply(text, parse_mode="HTML")


async def _resolve_user(message: Message, bot: Bot) -> int:
    """Resolve user ID from arguments."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id

    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "❌ <b>Usage:</b> <code>/command @username</code> or <code>/command user_id</code>\n"
            "Or reply to a user's message.",
            parse_mode="HTML"
        )
        return None

    target = args[1]
    
    if target.isdigit():
        return int(target)

    username = target.lstrip("@")
    all_users = await db.get_all_users()
    for u in all_users:
        if u.get('username', '').lower() == username.lower():
            return u['user_id']

    await message.reply(
        f"❌ User <code>{target}</code> not found.\n"
        f"<i>They must start the bot first.</i>",
        parse_mode="HTML"
    )
    return None
