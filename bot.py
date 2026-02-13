"""
╔══════════════════════════════════════════════════╗
║           SUPREME HOSTING BOT                     ║
║      Gadget Premium Host - @shuvohassan00         ║
║      GADGET PREMIUM ZONE - Production Ready       ║
╚══════════════════════════════════════════════════╝

Main entry point for the bot.
Requires: Python 3.10+, aiogram 3.x
"""

import asyncio
import logging
import os
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, OWNER_ID, BOT_NAME, UPLOAD_DIR, LOGS_DIR
from database import db
from middlewares.auth import AuthMiddleware
from handlers import get_all_routers
from services.process_manager import process_manager
from services.premium_scheduler import premium_scheduler

# ─────────── Logging Setup ───────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Reduce noise from libraries
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("aiosqlite").setLevel(logging.WARNING)


async def on_startup(bot: Bot):
    """Called when bot starts."""
    logger.info("═" * 50)
    logger.info(f"  🚀 {BOT_NAME} is starting...")
    logger.info("═" * 50)
    
    # Create directories
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Connect database
    await db.connect()
    logger.info("✅ Database connected")
    
    # Set up log callback for process manager
    async def log_callback(bot_id: int, message: str, log_type: str):
        try:
            await db.add_log(bot_id, message, log_type)
        except Exception:
            pass
    
    process_manager.set_log_callback(log_callback)
    logger.info("✅ Process manager initialized")
    
    # Start premium scheduler
    premium_scheduler.set_bot(bot)
    await premium_scheduler.start()
    logger.info("✅ Premium scheduler started")
    
    # Notify owner
    try:
        await bot.send_message(
            OWNER_ID,
            f"╔══════════════════════════╗\n"
            f"   🚀 <b>{BOT_NAME}</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"✅ Bot started successfully!\n\n"
            f"📊 <b>System Info:</b>\n"
            f"  • Python: {sys.version.split()[0]}\n"
            f"  • PID: {os.getpid()}\n"
            f"  • Platform: {sys.platform}\n\n"
            f"<i>All systems operational! 🟢</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not notify owner: {e}")
    
    logger.info(f"✅ {BOT_NAME} is fully operational!")


async def on_shutdown(bot: Bot):
    """Called when bot stops."""
    logger.info("🛑 Shutting down...")
    
    # Stop all hosted bots
    count = await process_manager.stop_all()
    logger.info(f"Stopped {count} running processes")
    
    # Update database
    running_bots = await db.get_all_running_bots()
    for b in running_bots:
        await db.update_bot_status(b['bot_id'], 'stopped')
    
    # Stop scheduler
    await premium_scheduler.stop()
    
    # Close database
    await db.close()
    
    # Notify owner
    try:
        await bot.send_message(
            OWNER_ID,
            f"🛑 <b>{BOT_NAME}</b> has been shut down.\n"
            f"Stopped {count} process(es).",
            parse_mode="HTML"
        )
    except:
        pass
    
    logger.info("✅ Shutdown complete")


async def main():
    """Main function."""
    
    # Validate token
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN is not set! Set it in config.py or as environment variable.")
        sys.exit(1)
    
    if OWNER_ID == 123456789:
        logger.warning("⚠️ OWNER_ID is default! Set your actual Telegram ID in config.py")
    
    # Initialize bot
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher
    dp = Dispatcher()
    
    # Register middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # Register all routers
    for r in get_all_routers():
        dp.include_router(r)
    
    # Register lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        loop.create_task(dp.stop_polling())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass
    
    logger.info("Starting polling...")
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "callback_query",
                "chat_member",
            ],
            drop_pending_updates=True
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
