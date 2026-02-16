import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

from config import Config
from database import db
from handlers.user_handlers import (
    start_command,
    help_command,
    profile_command,
    premium_info_command,
    button_callback
)
from handlers.hosting_handlers import (
    mybots_command,
    host_command,
    receive_file,
    receive_bot_name,
    cancel_hosting,
    install_module_command,
    bot_callback_handler,
    WAITING_FOR_FILE,
    WAITING_FOR_BOT_NAME
)
from handlers.admin_handlers import (
    admin_panel_command,
    add_admin_command,
    remove_admin_command,
    admin_list_command,
    add_premium_command,
    remove_premium_command,
    premium_list_command,
    ban_user_command,
    unban_user_command,
    broadcast_command,
    stats_admin_command
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

E = Config.EMOJI

async def error_handler(update: object, context) -> None:
    """Log errors caused by updates"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                f"{E['cross']} **An error occurred!**\n\n"
                f"Please try again or contact support.\n\n"
                f"Error: `{str(context.error)[:100]}`",
                parse_mode='Markdown'
            )
    except:
        pass

async def post_init(application: Application) -> None:
    """Post initialization tasks"""
    # Set bot commands
    commands = [
        ("start", "🚀 Start the bot"),
        ("help", "📖 Show help message"),
        ("host", "📤 Host a new bot"),
        ("mybots", "🤖 View your bots"),
        ("profile", "👤 Your profile"),
        ("install", "📦 Install Python module"),
        ("premium", "👑 Premium info"),
        ("admin", "👨‍💼 Admin panel (Admin only)"),
    ]
    
    await application.bot.set_my_commands(commands)
    
    # Send startup notification to owner
    try:
        await application.bot.send_message(
            chat_id=Config.OWNER_ID,
            text=f"{E['rocket']} **Bot Started Successfully!** {E['rocket']}\n\n"
                 f"{E['check']} All systems operational\n"
                 f"{E['gear']} Ready to host bots\n\n"
                 f"━━━━━━━━━━━━━━━━━━━━\n"
                 f"Developer: @shuvohassan00",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send startup notification: {e}")

def main():
    """Start the bot"""
    
    # Create application
    application = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # ========== USER HANDLERS ==========
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("premium", premium_info_command))
    
    # ========== HOSTING HANDLERS ==========
    application.add_handler(CommandHandler("mybots", mybots_command))
    application.add_handler(CommandHandler("install", install_module_command))
    
    # Host bot conversation handler
    host_conversation = ConversationHandler(
        entry_points=[CommandHandler("host", host_command)],
        states={
            WAITING_FOR_FILE: [
                MessageHandler(filters.Document.ALL, receive_file)
            ],
            WAITING_FOR_BOT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_bot_name)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_hosting)],
    )
    application.add_handler(host_conversation)
    
    # Handle direct file uploads (outside conversation)
    async def handle_direct_file(update: Update, context):
        """Handle files sent directly without /host command"""
        await update.message.reply_text(
            f"{E['info']} **File Received!**\n\n"
            f"To host this bot, please use the `/host` command first.\n\n"
            f"Then send your file.",
            parse_mode='Markdown'
        )
    
    application.add_handler(
        MessageHandler(
            filters.Document.ALL & ~filters.COMMAND,
            handle_direct_file
        )
    )
    
    # ========== ADMIN HANDLERS ==========
    application.add_handler(CommandHandler("admin", admin_panel_command))
    application.add_handler(CommandHandler("addadmin", add_admin_command))
    application.add_handler(CommandHandler("removeadmin", remove_admin_command))
    application.add_handler(CommandHandler("adminlist", admin_list_command))
    application.add_handler(CommandHandler("addpremium", add_premium_command))
    application.add_handler(CommandHandler("removepremium", remove_premium_command))
    application.add_handler(CommandHandler("premiumlist", premium_list_command))
    application.add_handler(CommandHandler("ban", ban_user_command))
    application.add_handler(CommandHandler("unban", unban_user_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("stats_admin", stats_admin_command))
    
    # ========== CALLBACK QUERY HANDLERS ==========
    # Combine all callback handlers
    async def unified_callback_handler(update: Update, context):
        """Handle all callback queries"""
        query = update.callback_query
        data = query.data
        
        # Bot control callbacks
        if data.startswith("bot_"):
            await bot_callback_handler(update, context)
        # User menu callbacks
        else:
            await button_callback(update, context)
    
    application.add_handler(CallbackQueryHandler(unified_callback_handler))
    
    # ========== ERROR HANDLER ==========
    application.add_error_handler(error_handler)
    
    # ========== BACKGROUND TASKS ==========
    async def check_premium_expiry(context):
        """Background task to check and remove expired premiums"""
        all_premium = db.get_all_premium_users()
        
        for user in all_premium:
            if user['premium_until']:
                from datetime import datetime
                premium_until = datetime.fromisoformat(user['premium_until'])
                
                if datetime.now() > premium_until:
                    # Remove premium
                    db.remove_premium(user['user_id'])
                    
                    # Notify user
                    try:
                        await context.bot.send_message(
                            chat_id=user['user_id'],
                            text=f"{E['info']} **Premium Expired**\n\n"
                                 f"Your premium membership has expired.\n\n"
                                 f"You are now on the free plan.\n"
                                 f"Contact @shuvohassan00 to renew.",
                            parse_mode='Markdown'
                        )
                    except:
                        pass
                    
                    logger.info(f"Removed expired premium from user {user['user_id']}")
    
    # Schedule premium check every hour
    job_queue = application.job_queue
    job_queue.run_repeating(check_premium_expiry, interval=3600, first=10)
    
    # ========== START BOT ==========
    logger.info("🚀 Bot is starting...")
    logger.info(f"📱 Bot Username: @{application.bot.username}")
    logger.info("✅ All handlers registered")
    logger.info("🔄 Polling for updates...")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
