"""
Supreme Hosting Bot - Process Management (Start/Stop/Restart/Logs)
"""

import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from utils.texts import Texts
from keyboards.inline import Keyboards
from services.process_manager import process_manager
from database import db
from config import OWNER_ID

router = Router()


# ─────────── My Bots List ───────────

@router.message(Command("mybots"))
async def cmd_mybots(message: Message, db_user: dict = None):
    bots = await db.get_user_bots(message.from_user.id)
    
    if not bots:
        await message.answer(
            Texts.no_bots(),
            parse_mode="HTML",
            reply_markup=Keyboards.back_to_menu()
        )
        return

    text = Texts.my_bots_header(len(bots))
    for bot_data in bots:
        # Sync status with process manager
        actual_running = process_manager.is_running(bot_data['bot_id'])
        if bot_data['status'] == 'running' and not actual_running:
            await db.update_bot_status(bot_data['bot_id'], 'stopped')
            bot_data['status'] = 'stopped'
        text += Texts.bot_info(bot_data)

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=Keyboards.bot_list(bots)
    )


@router.callback_query(F.data == "mybots")
async def cb_mybots(callback: CallbackQuery, db_user: dict = None):
    bots = await db.get_user_bots(callback.from_user.id)
    
    if not bots:
        await callback.message.edit_text(
            Texts.no_bots(),
            parse_mode="HTML",
            reply_markup=Keyboards.back_to_menu()
        )
        await callback.answer()
        return

    text = Texts.my_bots_header(len(bots))
    for bot_data in bots:
        actual_running = process_manager.is_running(bot_data['bot_id'])
        if bot_data['status'] == 'running' and not actual_running:
            await db.update_bot_status(bot_data['bot_id'], 'stopped')
            bot_data['status'] = 'stopped'
        text += Texts.bot_info(bot_data)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=Keyboards.bot_list(bots)
    )
    await callback.answer()


# ─────────── Bot Management ───────────

@router.callback_query(F.data.startswith("manage_"))
async def cb_manage_bot(callback: CallbackQuery, db_user: dict = None):
    bot_id = int(callback.data.split("_")[1])
    bot_data = await db.get_bot(bot_id)
    
    if not bot_data:
        await callback.answer("❌ Bot not found!", show_alert=True)
        return

    # Permission check
    if bot_data['user_id'] != callback.from_user.id and callback.from_user.id != OWNER_ID:
        await callback.answer("🔒 Not your bot!", show_alert=True)
        return

    # Sync status
    actual_running = process_manager.is_running(bot_id)
    if bot_data['status'] == 'running' and not actual_running:
        await db.update_bot_status(bot_id, 'stopped')
        bot_data['status'] = 'stopped'

    text = (
        f"╔══════════════════════════╗\n"
        f"   🤖 <b>Bot Management</b>\n"
        f"╚══════════════════════════╝\n\n"
        + Texts.bot_info(bot_data) +
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n<i>Choose an action below:</i>"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=Keyboards.bot_management(bot_id, bot_data['status'])
    )
    await callback.answer()


# ─────────── Start Bot ───────────

@router.callback_query(F.data.startswith("start_"))
async def cb_start_bot(callback: CallbackQuery, db_user: dict = None):
    bot_id = int(callback.data.split("_")[1])
    bot_data = await db.get_bot(bot_id)
    
    if not bot_data:
        await callback.answer("❌ Bot not found!", show_alert=True)
        return

    if bot_data['user_id'] != callback.from_user.id and callback.from_user.id != OWNER_ID:
        await callback.answer("🔒 Not your bot!", show_alert=True)
        return

    if process_manager.is_running(bot_id):
        await callback.answer("⚠️ Bot is already running!", show_alert=True)
        return

    await callback.answer("⏳ Starting bot...")
    
    # Determine working directory
    file_path = bot_data['file_path']
    working_dir = os.path.dirname(file_path)

    success, msg, pid = await process_manager.start_process(bot_id, file_path, working_dir)
    
    if success:
        await db.update_bot_status(bot_id, 'running', pid)
        await db.log_activity(callback.from_user.id, "bot_started", f"Bot #{bot_id}")
        
        await callback.message.edit_text(
            Texts.bot_started(bot_id, bot_data['original_name']),
            parse_mode="HTML",
            reply_markup=Keyboards.bot_management(bot_id, "running")
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Failed to Start!</b>\n\n"
            f"🆔 Bot ID: <code>{bot_id}</code>\n"
            f"⚠️ <b>Error:</b> {msg}",
            parse_mode="HTML",
            reply_markup=Keyboards.bot_management(bot_id, "stopped")
        )


# ─────────── Stop Bot ───────────

@router.callback_query(F.data.startswith("stop_"))
async def cb_stop_bot(callback: CallbackQuery, db_user: dict = None):
    bot_id = int(callback.data.split("_")[1])
    bot_data = await db.get_bot(bot_id)
    
    if not bot_data:
        await callback.answer("❌ Bot not found!", show_alert=True)
        return

    if bot_data['user_id'] != callback.from_user.id and callback.from_user.id != OWNER_ID:
        await callback.answer("🔒 Not your bot!", show_alert=True)
        return

    await callback.answer("⏳ Stopping bot...")
    
    success, msg = await process_manager.stop_process(bot_id)
    await db.update_bot_status(bot_id, 'stopped')
    await db.log_activity(callback.from_user.id, "bot_stopped", f"Bot #{bot_id}")
    
    await callback.message.edit_text(
        Texts.bot_stopped(bot_id, bot_data['original_name']),
        parse_mode="HTML",
        reply_markup=Keyboards.bot_management(bot_id, "stopped")
    )


# ─────────── Restart Bot ───────────

@router.callback_query(F.data.startswith("restart_"))
async def cb_restart_bot(callback: CallbackQuery, db_user: dict = None):
    bot_id = int(callback.data.split("_")[1])
    bot_data = await db.get_bot(bot_id)
    
    if not bot_data:
        await callback.answer("❌ Bot not found!", show_alert=True)
        return

    if bot_data['user_id'] != callback.from_user.id and callback.from_user.id != OWNER_ID:
        await callback.answer("🔒 Not your bot!", show_alert=True)
        return

    await callback.answer("⏳ Restarting bot...")
    
    file_path = bot_data['file_path']
    working_dir = os.path.dirname(file_path)
    
    await process_manager.stop_process(bot_id)
    
    import asyncio
    await asyncio.sleep(1)
    
    success, msg, pid = await process_manager.start_process(bot_id, file_path, working_dir)
    
    if success:
        await db.update_bot_status(bot_id, 'running', pid)
        await db.log_activity(callback.from_user.id, "bot_restarted", f"Bot #{bot_id}")
        
        await callback.message.edit_text(
            Texts.bot_restarted(bot_id, bot_data['original_name']),
            parse_mode="HTML",
            reply_markup=Keyboards.bot_management(bot_id, "running")
        )
    else:
        await db.update_bot_status(bot_id, 'stopped')
        await callback.message.edit_text(
            f"❌ <b>Restart Failed!</b>\n\n⚠️ {msg}",
            parse_mode="HTML",
            reply_markup=Keyboards.bot_management(bot_id, "stopped")
        )


# ─────────── View Logs ───────────

@router.callback_query(F.data.startswith("logs_"))
async def cb_view_logs(callback: CallbackQuery, db_user: dict = None):
    bot_id = int(callback.data.split("_")[1])
    bot_data = await db.get_bot(bot_id)
    
    if not bot_data:
        await callback.answer("❌ Bot not found!", show_alert=True)
        return

    if bot_data['user_id'] != callback.from_user.id and callback.from_user.id != OWNER_ID:
        await callback.answer("🔒 Not your bot!", show_alert=True)
        return

    # Get logs from process manager (live) and database
    live_logs = process_manager.get_recent_logs(bot_id, 30)
    db_logs = await db.get_logs(bot_id, 20)
    
    text = Texts.logs_header(bot_id, bot_data['original_name'])
    
    if live_logs:
        text += "<b>📡 Live Output:</b>\n<pre>"
        for log_line in live_logs[-30:]:
            # Truncate long lines
            if len(log_line) > 100:
                log_line = log_line[:100] + "..."
            text += f"{log_line}\n"
        text += "</pre>\n"
    elif db_logs:
        text += "<b>📋 Recent Logs:</b>\n<pre>"
        for log in reversed(db_logs[-20:]):
            msg = log['message'][:100]
            text += f"[{log['log_type'].upper()}] {msg}\n"
        text += "</pre>\n"
    else:
        text += Texts.no_logs()

    # Trim if too long for Telegram
    if len(text) > 4000:
        text = text[:3900] + "\n...</pre>\n\n<i>⚠️ Logs truncated.</i>"

    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=Keyboards.logs_keyboard(bot_id)
        )
    except Exception:
        # If message is same, ignore
        pass
    await callback.answer()


@router.message(Command("logs"))
async def cmd_logs(message: Message, db_user: dict = None):
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "📋 <b>Usage:</b> <code>/logs &lt;bot_id&gt;</code>",
            parse_mode="HTML"
        )
        return
    
    try:
        bot_id = int(args[1])
    except ValueError:
        await message.reply("❌ Invalid bot ID!", parse_mode="HTML")
        return

    bot_data = await db.get_bot(bot_id)
    if not bot_data:
        await message.reply("❌ Bot not found!", parse_mode="HTML")
        return

    if bot_data['user_id'] != message.from_user.id and message.from_user.id != OWNER_ID:
        await message.reply(Texts.not_authorized(), parse_mode="HTML")
        return

    live_logs = process_manager.get_recent_logs(bot_id, 40)
    text = Texts.logs_header(bot_id, bot_data['original_name'])
    
    if live_logs:
        text += "<pre>"
        for log_line in live_logs[-40:]:
            if len(log_line) > 100:
                log_line = log_line[:100] + "..."
            text += f"{log_line}\n"
        text += "</pre>"
    else:
        text += Texts.no_logs()

    if len(text) > 4000:
        text = text[:3900] + "\n...</pre>"

    await message.reply(
        text,
        parse_mode="HTML",
        reply_markup=Keyboards.logs_keyboard(bot_id)
    )


# ─────────── Clear Logs ───────────

@router.callback_query(F.data.startswith("clearlogs_"))
async def cb_clear_logs(callback: CallbackQuery, db_user: dict = None):
    bot_id = int(callback.data.split("_")[1])
    bot_data = await db.get_bot(bot_id)
    
    if not bot_data:
        await callback.answer("❌ Bot not found!", show_alert=True)
        return

    if bot_data['user_id'] != callback.from_user.id and callback.from_user.id != OWNER_ID:
        await callback.answer("🔒 Not your bot!", show_alert=True)
        return

    await db.clear_logs(bot_id)
    # Clear live buffer too
    managed = process_manager._processes.get(bot_id)
    if managed:
        managed.log_buffer.clear()

    await callback.answer("🗑️ Logs cleared!", show_alert=True)
    
    text = Texts.logs_header(bot_id, bot_data['original_name']) + Texts.no_logs()
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=Keyboards.logs_keyboard(bot_id)
    )


# ─────────── Delete Bot ───────────

@router.callback_query(F.data.startswith("delete_"))
async def cb_delete_confirm(callback: CallbackQuery, db_user: dict = None):
    bot_id = int(callback.data.split("_")[1])
    bot_data = await db.get_bot(bot_id)
    
    if not bot_data:
        await callback.answer("❌ Bot not found!", show_alert=True)
        return

    if bot_data['user_id'] != callback.from_user.id and callback.from_user.id != OWNER_ID:
        await callback.answer("🔒 Not your bot!", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ <b>Confirm Deletion</b>\n\n"
        f"Are you sure you want to delete bot <code>#{bot_id}</code>?\n"
        f"📄 <code>{bot_data['original_name']}</code>\n\n"
        f"<b>This action cannot be undone!</b>",
        parse_mode="HTML",
        reply_markup=Keyboards.confirm_delete(bot_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirmdelete_"))
async def cb_confirm_delete(callback: CallbackQuery, db_user: dict = None):
    bot_id = int(callback.data.split("_")[1])
    bot_data = await db.get_bot(bot_id)
    
    if not bot_data:
        await callback.answer("❌ Bot not found!", show_alert=True)
        return

    if bot_data['user_id'] != callback.from_user.id and callback.from_user.id != OWNER_ID:
        await callback.answer("🔒 Not your bot!", show_alert=True)
        return

    # Stop process if running
    await process_manager.stop_process(bot_id)
    
    # Delete files
    import shutil
    file_dir = os.path.dirname(bot_data['file_path'])
    if os.path.exists(file_dir):
        shutil.rmtree(file_dir, ignore_errors=True)
    
    # Delete from database
    await db.delete_bot(bot_id)
    await db.log_activity(callback.from_user.id, "bot_deleted", f"Bot #{bot_id}")

    await callback.message.edit_text(
        Texts.bot_deleted(bot_id),
        parse_mode="HTML",
        reply_markup=Keyboards.back_to_menu()
    )
    await callback.answer("🗑️ Bot deleted!", show_alert=True)
