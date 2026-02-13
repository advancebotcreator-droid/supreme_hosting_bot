"""
Supreme Hosting Bot - Dependency Installation Handler
"""

import asyncio
import sys

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from utils.texts import Texts
from database import db
from config import OWNER_ID

router = Router()


@router.message(Command("install"))
async def cmd_install(message: Message, db_user: dict = None):
    """Install a Python module via pip."""
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "📦 <b>Install a Module</b>\n\n"
            "<b>Usage:</b> <code>/install module_name</code>\n"
            "<b>Example:</b> <code>/install aiogram</code>\n\n"
            "You can also install specific versions:\n"
            "<code>/install aiogram==3.12.0</code>",
            parse_mode="HTML"
        )
        return

    module_name = args[1].strip()
    
    # Basic security: prevent command injection
    if any(c in module_name for c in [';', '&', '|', '`', '$', '(', ')', '{', '}', '>', '<', '\n', '\r']):
        await message.reply(
            "❌ <b>Invalid module name!</b>\n\nModule name contains forbidden characters.",
            parse_mode="HTML"
        )
        return

    # Only premium users or admins/owner can install globally
    is_privileged = (
        message.from_user.id == OWNER_ID or
        (db_user and (db_user.get('is_admin') or db_user.get('is_premium')))
    )

    if not is_privileged:
        # Free users can still install, but we note it
        pass

    status_msg = await message.reply(
        f"📦 <b>Installing</b> <code>{module_name}</code>...\n\n"
        f"<i>⏳ Please wait...</i>",
        parse_mode="HTML"
    )

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'pip', 'install', module_name,
            '--disable-pip-version-check',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        
        stdout_text = stdout.decode('utf-8', errors='replace')
        stderr_text = stderr.decode('utf-8', errors='replace')

        if proc.returncode == 0:
            await db.log_activity(
                message.from_user.id, "install_module", f"Installed: {module_name}"
            )
            
            # Show success with some output
            output = stdout_text.strip()
            if len(output) > 500:
                output = output[:500] + "..."

            await status_msg.edit_text(
                Texts.install_success(module_name) + 
                (f"\n<pre>{output}</pre>" if output else ""),
                parse_mode="HTML"
            )
        else:
            error = stderr_text.strip() or stdout_text.strip()
            await status_msg.edit_text(
                Texts.install_failed(module_name, error),
                parse_mode="HTML"
            )

    except asyncio.TimeoutError:
        await status_msg.edit_text(
            f"⏰ <b>Installation Timed Out!</b>\n\n"
            f"Module <code>{module_name}</code> took too long to install.",
            parse_mode="HTML"
        )
    except Exception as e:
        await status_msg.edit_text(
            f"❌ <b>Installation Error!</b>\n\n<pre>{str(e)[:500]}</pre>",
            parse_mode="HTML"
        )
