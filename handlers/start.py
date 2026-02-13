"""
Supreme Hosting Bot - Start & Help Handlers
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from utils.texts import Texts
from keyboards.inline import Keyboards
from database import db
from config import OWNER_ID

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: dict = None):
    await message.answer(
        Texts.welcome(message.from_user.full_name, message.from_user.id),
        parse_mode="HTML",
        reply_markup=Keyboards.main_menu(),
        disable_web_page_preview=True
    )


@router.callback_query(F.data == "start")
async def cb_start(callback: CallbackQuery, db_user: dict = None):
    await callback.message.edit_text(
        Texts.welcome(callback.from_user.full_name, callback.from_user.id),
        parse_mode="HTML",
        reply_markup=Keyboards.main_menu(),
        disable_web_page_preview=True
    )
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message, db_user: dict = None):
    await message.answer(
        Texts.help_text(),
        parse_mode="HTML",
        reply_markup=Keyboards.back_to_menu(),
        disable_web_page_preview=True
    )


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery, db_user: dict = None):
    await callback.message.edit_text(
        Texts.help_text(),
        parse_mode="HTML",
        reply_markup=Keyboards.back_to_menu(),
        disable_web_page_preview=True
    )
    await callback.answer()


@router.message(Command("profile"))
async def cmd_profile(message: Message, db_user: dict = None):
    if not db_user:
        db_user = await db.get_user(message.from_user.id)
    bot_count = await db.get_user_bot_count(message.from_user.id)
    await message.answer(
        Texts.profile(db_user, bot_count),
        parse_mode="HTML",
        reply_markup=Keyboards.back_to_menu()
    )


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery, db_user: dict = None):
    if not db_user:
        db_user = await db.get_user(callback.from_user.id)
    bot_count = await db.get_user_bot_count(callback.from_user.id)
    await callback.message.edit_text(
        Texts.profile(db_user, bot_count),
        parse_mode="HTML",
        reply_markup=Keyboards.back_to_menu()
    )
    await callback.answer()


@router.message(Command("panel"))
async def cmd_panel(message: Message, db_user: dict = None):
    user_id = message.from_user.id
    if user_id == OWNER_ID:
        await message.answer(
            "🔐 <b>Owner Control Panel</b>",
            parse_mode="HTML",
            reply_markup=Keyboards.owner_panel()
        )
    elif db_user and db_user.get('is_admin'):
        await message.answer(
            "🛡️ <b>Admin Control Panel</b>",
            parse_mode="HTML",
            reply_markup=Keyboards.admin_panel()
        )
    else:
        await message.answer(Texts.not_authorized(), parse_mode="HTML")
