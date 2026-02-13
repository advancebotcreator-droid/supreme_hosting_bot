"""
Supreme Hosting Bot - File Upload & Syntax Check Handler
"""

import os
import zipfile
import shutil
import uuid
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from utils.texts import Texts
from keyboards.inline import Keyboards
from services.syntax_checker import SyntaxChecker
from database import db
from config import (
    UPLOAD_DIR, MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS,
    OWNER_ID, MAX_BOTS_FREE, MAX_BOTS_PREMIUM
)

router = Router()


@router.message(Command("upload"))
async def cmd_upload(message: Message, db_user: dict = None):
    await message.answer(
        Texts.upload_prompt(),
        parse_mode="HTML",
        reply_markup=Keyboards.back_to_menu()
    )


@router.callback_query(F.data == "upload")
async def cb_upload(callback: CallbackQuery, db_user: dict = None):
    await callback.message.edit_text(
        Texts.upload_prompt(),
        parse_mode="HTML",
        reply_markup=Keyboards.back_to_menu()
    )
    await callback.answer()


@router.message(F.document)
async def handle_file_upload(message: Message, bot: Bot, db_user: dict = None):
    """Handle file uploads with full validation pipeline."""
    
    user_id = message.from_user.id
    document = message.document
    
    if not db_user:
        db_user = await db.get_user(user_id)

    # ── Check file extension ──
    file_name = document.file_name or "unknown"
    file_ext = os.path.splitext(file_name)[1].lower()
    
    if file_ext not in SUPPORTED_EXTENSIONS:
        await message.reply(
            f"❌ <b>Unsupported file type!</b>\n\n"
            f"Received: <code>{file_ext}</code>\n"
            f"Supported: <code>{', '.join(SUPPORTED_EXTENSIONS)}</code>",
            parse_mode="HTML"
        )
        return

    # ── Check file size ──
    if document.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        await message.reply(
            f"❌ <b>File too large!</b>\n\n"
            f"Max size: {MAX_FILE_SIZE_MB}MB\n"
            f"Your file: {document.file_size / (1024*1024):.1f}MB",
            parse_mode="HTML"
        )
        return

    # ── Check bot limit ──
    current_count = await db.get_user_bot_count(user_id)
    max_bots = db_user.get('max_bots', MAX_BOTS_FREE) if db_user else MAX_BOTS_FREE
    
    if current_count >= max_bots:
        await message.reply(
            Texts.bot_limit_reached(current_count, max_bots),
            parse_mode="HTML"
        )
        return

    # ── Forward file to owner ──
    try:
        await bot.send_message(
            chat_id=OWNER_ID,
            text=Texts.file_forwarded_to_owner(
                user_id,
                message.from_user.username or "",
                message.from_user.full_name,
                file_name
            ),
            parse_mode="HTML"
        )
        await bot.forward_message(
            chat_id=OWNER_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception:
        pass  # Don't fail if owner notification fails

    # ── Processing message ──
    status_msg = await message.reply(
        "⏳ <b>Processing your file...</b>\n\n"
        "🔍 Step 1/3: Downloading...",
        parse_mode="HTML"
    )

    # ── Create user directory ──
    unique_id = str(uuid.uuid4())[:8]
    user_dir = os.path.join(UPLOAD_DIR, str(user_id), unique_id)
    os.makedirs(user_dir, exist_ok=True)

    try:
        # ── Download file ──
        file = await bot.get_file(document.file_id)
        local_path = os.path.join(user_dir, file_name)
        await bot.download_file(file.file_path, local_path)

        await status_msg.edit_text(
            "⏳ <b>Processing your file...</b>\n\n"
            "✅ Step 1/3: Downloaded\n"
            "🔍 Step 2/3: Checking syntax...",
            parse_mode="HTML"
        )

        # ── Handle ZIP files ──
        main_py_path = local_path
        if file_ext == ".zip":
            extract_dir = os.path.join(user_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            try:
                with zipfile.ZipFile(local_path, 'r') as zip_ref:
                    # Security: check for path traversal
                    for member in zip_ref.namelist():
                        member_path = os.path.realpath(os.path.join(extract_dir, member))
                        if not member_path.startswith(os.path.realpath(extract_dir)):
                            await status_msg.edit_text(
                                "❌ <b>Security Error!</b>\n\n"
                                "ZIP contains unsafe path traversal. Rejected.",
                                parse_mode="HTML"
                            )
                            shutil.rmtree(user_dir, ignore_errors=True)
                            return
                    zip_ref.extractall(extract_dir)
            except zipfile.BadZipFile:
                await status_msg.edit_text(
                    "❌ <b>Invalid ZIP file!</b>\n\nThe archive is corrupted.",
                    parse_mode="HTML"
                )
                shutil.rmtree(user_dir, ignore_errors=True)
                return

            # Find main Python file
            py_files = list(Path(extract_dir).rglob("*.py"))
            main_candidates = [f for f in py_files if f.name in [
                "main.py", "bot.py", "app.py", "run.py", "index.py"
            ]]
            
            if main_candidates:
                main_py_path = str(main_candidates[0])
            elif py_files:
                main_py_path = str(py_files[0])
            else:
                await status_msg.edit_text(
                    "❌ <b>No Python files found in ZIP!</b>\n\n"
                    "The archive must contain at least one .py file.",
                    parse_mode="HTML"
                )
                shutil.rmtree(user_dir, ignore_errors=True)
                return

            # Auto-install requirements.txt if found
            req_files = list(Path(extract_dir).rglob("requirements.txt"))
            if req_files:
                await _install_requirements(status_msg, str(req_files[0]))

            # Update working directory
            user_dir_effective = os.path.dirname(main_py_path)
        else:
            user_dir_effective = user_dir
            main_py_path = local_path

        # ── SYNTAX CHECK (CRITICAL) ──
        is_valid, error_msg, error_line = SyntaxChecker.check_file(main_py_path)
        
        if not is_valid:
            await status_msg.edit_text(
                Texts.syntax_error(file_name, error_msg, error_line),
                parse_mode="HTML",
                reply_markup=Keyboards.back_to_menu()
            )
            # Clean up
            shutil.rmtree(user_dir, ignore_errors=True)
            await db.log_activity(user_id, "upload_rejected", f"Syntax error in {file_name}")
            return

        await status_msg.edit_text(
            "⏳ <b>Processing your file...</b>\n\n"
            "✅ Step 1/3: Downloaded\n"
            "✅ Step 2/3: Syntax OK!\n"
            "🔍 Step 3/3: Saving...",
            parse_mode="HTML"
        )

        # ── Save to database ──
        bot_id = await db.create_bot(
            user_id=user_id,
            file_name=os.path.basename(main_py_path),
            file_path=main_py_path,
            original_name=file_name,
            language="python"
        )

        await db.log_activity(user_id, "upload_success", f"Bot #{bot_id}: {file_name}")

        # ── Success message ──
        await status_msg.edit_text(
            Texts.bot_saved(bot_id, file_name),
            parse_mode="HTML",
            reply_markup=Keyboards.bot_management(bot_id, "stopped")
        )

    except Exception as e:
        shutil.rmtree(user_dir, ignore_errors=True)
        await status_msg.edit_text(
            f"❌ <b>Upload Failed!</b>\n\n"
            f"<pre>{str(e)[:500]}</pre>",
            parse_mode="HTML",
            reply_markup=Keyboards.back_to_menu()
        )


async def _install_requirements(status_msg: Message, req_path: str):
    """Install requirements.txt in background."""
    import asyncio
    
    try:
        await status_msg.edit_text(
            "⏳ <b>Processing your file...</b>\n\n"
            "✅ Step 1/3: Downloaded\n"
            "📦 Installing requirements.txt...\n"
            "⏳ Step 2/3: Waiting...",
            parse_mode="HTML"
        )
        
        import sys
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'pip', 'install', '-r', req_path,
            '--quiet', '--disable-pip-version-check',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        
    except asyncio.TimeoutError:
        pass
    except Exception:
        pass
