import os
import zipfile
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import Config
from database import db
from utils.decorators import track_user, check_banned
from utils.code_validator import CodeValidator
from utils.process_manager import process_manager

E = Config.EMOJI

# Conversation states
WAITING_FOR_FILE, WAITING_FOR_BOT_NAME, WAITING_FOR_MODULE_NAME = range(3)

@track_user
@check_banned
async def mybots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's hosted bots"""
    user_id = update.effective_user.id
    user_bots = db.get_user_bots(user_id)
    
    if not user_bots:
        text = f"""
{E['robot']} **My Bots**

You haven't hosted any bots yet!

{E['upload']} **How to host a bot:**
1. Send me your .py or .js file
2. I'll validate the code
3. If valid, your bot will be hosted!

Or use /host command to start.
        """
        
        keyboard = [[
            InlineKeyboardButton(f"{E['upload']} Host New Bot", callback_data="host_new_bot")
        ]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return
    
    text = f"{E['robot']} **Your Hosted Bots** ({len(user_bots)})\n\n"
    
    keyboard = []
    
    for i, bot in enumerate(user_bots, 1):
        status_emoji = {
            'running': '🟢',
            'stopped': '🔴',
            'error': '⚠️'
        }.get(bot['status'], '⚪')
        
        text += f"{i}. {status_emoji} **{bot['bot_name']}**\n"
        text += f"   ├ File: `{bot['file_name']}`\n"
        text += f"   ├ Type: {bot['file_type'].upper()}\n"
        text += f"   ├ Status: {bot['status'].title()}\n"
        text += f"   └ Created: {bot['created_date'][:10]}\n\n"
        
        # Add control buttons for each bot
        keyboard.append([
            InlineKeyboardButton(
                f"{'⏹️ Stop' if bot['status'] == 'running' else '▶️ Start'} #{i}",
                callback_data=f"bot_toggle_{bot['bot_id']}"
            ),
            InlineKeyboardButton(f"🔄 Restart #{i}", callback_data=f"bot_restart_{bot['bot_id']}"),
        ])
        keyboard.append([
            InlineKeyboardButton(f"📊 Status #{i}", callback_data=f"bot_status_{bot['bot_id']}"),
            InlineKeyboardButton(f"📝 Logs #{i}", callback_data=f"bot_logs_{bot['bot_id']}"),
            InlineKeyboardButton(f"🗑️ Delete #{i}", callback_data=f"bot_delete_{bot['bot_id']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(f"{E['upload']} Host New Bot", callback_data="host_new_bot"),
        InlineKeyboardButton(f"🔄 Refresh", callback_data="my_bots")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

@track_user
@check_banned
async def host_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start bot hosting conversation"""
    user_id = update.effective_user.id
    user_bots = db.get_user_bots(user_id)
    is_premium = db.is_premium(user_id)
    
    max_bots = Config.MAX_BOTS_PREMIUM if is_premium else Config.MAX_BOTS_FREE
    
    if len(user_bots) >= max_bots:
        await update.message.reply_text(
            f"{E['warning']} **Bot Limit Reached!**\n\n"
            f"You have reached the maximum number of bots ({max_bots}).\n"
            f"{'Please delete a bot before hosting a new one.' if not is_premium else 'Please delete a bot before hosting a new one.'}\n\n"
            f"{'💎 Upgrade to Premium to host up to 10 bots!' if not is_premium else ''}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    text = f"""
{E['upload']} **Host New Bot**

Please send me your bot file:

{E['check']} **Supported formats:**
├ Python files (.py)
├ JavaScript files (.js)
└ ZIP archives (.zip)

{E['info']} **File limits:**
├ Free: {Config.MAX_FILE_SIZE_FREE // (1024*1024)}MB
└ Premium: {Config.MAX_FILE_SIZE_PREMIUM // (1024*1024)}MB

{E['fire']} **What happens next:**
1. I'll validate your code for syntax errors
2. Show you any issues found
3. If valid, host your bot automatically!

Send your file now or /cancel to abort.
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')
    
    return WAITING_FOR_FILE

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle received file for hosting"""
    user_id = update.effective_user.id
    is_premium = db.is_premium(user_id)
    
    # Get file
    if update.message.document:
        file = update.message.document
    else:
        await update.message.reply_text(
            f"{E['cross']} Please send a valid file (.py, .js, or .zip)",
            parse_mode='Markdown'
        )
        return WAITING_FOR_FILE
    
    # Check file size
    max_size = Config.MAX_FILE_SIZE_PREMIUM if is_premium else Config.MAX_FILE_SIZE_FREE
    
    if file.file_size > max_size:
        await update.message.reply_text(
            f"{E['cross']} **File Too Large!**\n\n"
            f"Your file: {file.file_size // (1024*1024)}MB\n"
            f"Your limit: {max_size // (1024*1024)}MB\n\n"
            f"{'💎 Upgrade to Premium for 50MB limit!' if not is_premium else 'Please reduce file size.'}",
            parse_mode='Markdown'
        )
        return WAITING_FOR_FILE
    
    # Check file extension
    file_name = file.file_name
    file_ext = file_name.split('.')[-1].lower()
    
    if file_ext not in ['py', 'js', 'zip']:
        await update.message.reply_text(
            f"{E['cross']} **Invalid File Type!**\n\n"
            f"Supported: .py, .js, .zip\n"
            f"Your file: .{file_ext}",
            parse_mode='Markdown'
        )
        return WAITING_FOR_FILE
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        f"{E['gear']} **Processing your file...**\n\n"
        f"├ Downloading file...\n"
        f"├ Validating code...\n"
        f"└ Please wait...",
        parse_mode='Markdown'
    )
    
    try:
        # Download file
        file_obj = await context.bot.get_file(file.file_id)
        
        # Create user directory
        user_dir = os.path.join(Config.HOSTED_BOTS_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(user_dir, file_name)
        await file_obj.download_to_drive(file_path)
        
        # Validate code
        if file_ext == 'zip':
            # Extract and validate zip
            validation_result = await validate_zip_file(file_path)
        else:
            # Validate single file
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            file_type = 'python' if file_ext == 'py' else 'javascript'
            validation_result = CodeValidator.get_detailed_error_report(code, file_type)
        
        await processing_msg.edit_text(
            f"{E['check']} **Validation Complete!**\n\n{validation_result}",
            parse_mode='Markdown'
        )
        
        # If validation failed, stop here
        if '❌' in validation_result:
            # Notify owner about failed upload
            await notify_owner_file_upload(context, update.effective_user, file_name, False, validation_result)
            return ConversationHandler.END
        
        # Store file info in context for next step
        context.user_data['file_info'] = {
            'file_name': file_name,
            'file_path': file_path,
            'file_type': file_type if file_ext != 'zip' else 'python',
            'file_size': file.file_size
        }
        
        # Ask for bot name
        await update.message.reply_text(
            f"{E['robot']} **Give your bot a name:**\n\n"
            f"This will help you identify your bot.\n"
            f"Example: My Awesome Bot\n\n"
            f"Send the name or /cancel",
            parse_mode='Markdown'
        )
        
        return WAITING_FOR_BOT_NAME
        
    except Exception as e:
        await processing_msg.edit_text(
            f"{E['cross']} **Error processing file:**\n\n`{str(e)}`",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def validate_zip_file(zip_path: str) -> str:
    """Validate ZIP file contents"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract to temp directory
            temp_dir = tempfile.mkdtemp()
            zip_ref.extractall(temp_dir)
            
            # Find main file (main.py or index.js)
            main_files = ['main.py', 'bot.py', 'index.js', 'main.js']
            main_file = None
            
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file in main_files:
                        main_file = os.path.join(root, file)
                        break
                if main_file:
                    break
            
            if not main_file:
                return "❌ **No main file found!**\n\nPlease include main.py or index.js in your ZIP."
            
            # Validate main file
            with open(main_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            file_type = 'python' if main_file.endswith('.py') else 'javascript'
            return CodeValidator.get_detailed_error_report(code, file_type)
            
    except Exception as e:
        return f"❌ **Error extracting ZIP:**\n\n`{str(e)}`"

async def receive_bot_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive bot name and complete hosting"""
    bot_name = update.message.text.strip()
    
    if len(bot_name) < 3 or len(bot_name) > 50:
        await update.message.reply_text(
            f"{E['cross']} Bot name must be between 3-50 characters.\n\nTry again:",
            parse_mode='Markdown'
        )
        return WAITING_FOR_BOT_NAME
    
    # Get file info
    file_info = context.user_data.get('file_info')
    if not file_info:
        await update.message.reply_text(
            f"{E['cross']} Session expired. Please start again with /host",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Save to database
    user_id = update.effective_user.id
    bot_id = db.add_hosted_bot(
        user_id=user_id,
        bot_name=bot_name,
        file_name=file_info['file_name'],
        file_path=file_info['file_path'],
        file_type=file_info['file_type'],
        file_size=file_info['file_size']
    )
    
    success_text = f"""
{E['party']} **Bot Hosted Successfully!** {E['party']}

{E['robot']} **Bot Details:**
├ Name: {bot_name}
├ File: `{file_info['file_name']}`
├ Type: {file_info['file_type'].upper()}
├ Size: {file_info['file_size'] // 1024}KB
└ Bot ID: #{bot_id}

{E['fire']} **Next Steps:**
├ Use /start_bot to run your bot
├ Use /mybots to manage all bots
└ Use /bot_status to monitor

{E['info']} **Useful Commands:**
├ /install <module> - Install dependencies
├ /bot_logs - View bot output
└ /help - Full command list

Your bot is ready to run! 🚀
    """
    
    keyboard = [
        [
            InlineKeyboardButton(f"▶️ Start Bot", callback_data=f"bot_toggle_{bot_id}"),
            InlineKeyboardButton(f"📊 Status", callback_data=f"bot_status_{bot_id}")
        ],
        [
            InlineKeyboardButton(f"{E['robot']} My Bots", callback_data="my_bots")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(success_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    # Notify owner about successful upload
    await notify_owner_file_upload(
        context, 
        update.effective_user, 
        file_info['file_name'], 
        True,
        file_path=file_info['file_path']
    )
    
    # Clear context
    context.user_data.clear()
    
    return ConversationHandler.END

async def notify_owner_file_upload(context, user, file_name, success, validation_result=None, file_path=None):
    """Notify owner about file uploads"""
    status = "✅ Successfully Hosted" if success else "❌ Validation Failed"
    
    notification = f"""
{E['bell']} **New Bot Upload**

{status}

{E['user']} **User Details:**
├ ID: `{user.id}`
├ Name: {user.first_name}
└ Username: @{user.username or 'No username'}

{E['file']} **File Details:**
├ Name: `{file_name}`
└ Status: {status}

{validation_result if validation_result and not success else ''}
    """
    
    try:
        await context.bot.send_message(
            chat_id=Config.OWNER_ID,
            text=notification,
            parse_mode='Markdown'
        )
        
        # Send file to owner if successful
        if success and file_path and os.path.exists(file_path):
            await context.bot.send_document(
                chat_id=Config.OWNER_ID,
                document=open(file_path, 'rb'),
                caption=f"📦 Uploaded by: {user.first_name} (@{user.username or user.id})"
            )
    except:
        pass

async def cancel_hosting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel hosting conversation"""
    context.user_data.clear()
    await update.message.reply_text(
        f"{E['cross']} Bot hosting cancelled.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

@track_user
@check_banned
async def install_module_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start module installation"""
    if not context.args:
        await update.message.reply_text(
            f"{E['package']} **Install Python Module**\n\n"
            f"Usage: `/install <module_name>`\n\n"
            f"Example:\n"
            f"`/install python-telegram-bot`\n"
            f"`/install requests`\n"
            f"`/install aiogram`",
            parse_mode='Markdown'
        )
        return
    
    module_name = ' '.join(context.args)
    
    installing_msg = await update.message.reply_text(
        f"{E['gear']} **Installing module...**\n\n"
        f"Module: `{module_name}`\n"
        f"This may take a few minutes...",
        parse_mode='Markdown'
    )
    
    # Install module
    success, message = process_manager.install_module(module_name)
    
    await installing_msg.edit_text(
        f"{'✅' if success else '❌'} **Installation {'Complete' if success else 'Failed'}**\n\n"
        f"{message}",
        parse_mode='Markdown'
    )

# Bot control callbacks
async def bot_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot control callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("bot_toggle_"):
        bot_id = int(data.split("_")[2])
        await toggle_bot(query, context, bot_id, user_id)
    
    elif data.startswith("bot_restart_"):
        bot_id = int(data.split("_")[2])
        await restart_bot(query, context, bot_id, user_id)
    
    elif data.startswith("bot_status_"):
        bot_id = int(data.split("_")[2])
        await show_bot_status(query, context, bot_id, user_id)
    
    elif data.startswith("bot_logs_"):
        bot_id = int(data.split("_")[2])
        await show_bot_logs(query, context, bot_id, user_id)
    
    elif data.startswith("bot_delete_"):
        bot_id = int(data.split("_")[2])
        await delete_bot(query, context, bot_id, user_id)
    
    elif data == "my_bots":
        # Refresh mybots
        user_bots = db.get_user_bots(user_id)
        
        if not user_bots:
            text = f"{E['robot']} You have no bots hosted."
        else:
            text = f"{E['robot']} **Your Hosted Bots** ({len(user_bots)})\n\n"
            keyboard = []
            
            for i, bot in enumerate(user_bots, 1):
                status_emoji = {
                    'running': '🟢',
                    'stopped': '🔴',
                    'error': '⚠️'
                }.get(bot['status'], '⚪')
                
                text += f"{i}. {status_emoji} **{bot['bot_name']}**\n"
                text += f"   └ Status: {bot['status'].title()}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"{'⏹️ Stop' if bot['status'] == 'running' else '▶️ Start'} #{i}",
                        callback_data=f"bot_toggle_{bot['bot_id']}"
                    ),
                    InlineKeyboardButton(f"📊 Status #{i}", callback_data=f"bot_status_{bot['bot_id']}"),
                ])
            
            keyboard.append([
                InlineKeyboardButton(f"🔄 Refresh", callback_data="my_bots")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def toggle_bot(query, context, bot_id, user_id):
    """Start/Stop bot"""
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != user_id:
        await query.edit_message_text(f"{E['cross']} Bot not found or access denied.")
        return
    
    if bot['status'] == 'running':
        # Stop bot
        success, message = process_manager.stop_bot(bot_id, bot['process_id'])
        if success:
            db.update_bot_status(bot_id, 'stopped')
    else:
        # Start bot
        success, message, process_id = process_manager.start_bot(
            bot_id, bot['file_path'], bot['file_type']
        )
        if success:
            db.update_bot_status(bot_id, 'running', process_id)
    
    await query.answer(message)
    
    # Refresh display
    await query.message.reply_text(message, parse_mode='Markdown')

async def restart_bot(query, context, bot_id, user_id):
    """Restart bot"""
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != user_id:
        await query.edit_message_text(f"{E['cross']} Bot not found or access denied.")
        return
    
    success, message, process_id = process_manager.restart_bot(
        bot_id, bot['process_id'], bot['file_path'], bot['file_type']
    )
    
    if success:
        db.update_bot_status(bot_id, 'running', process_id)
    
    await query.answer(message)
    await query.message.reply_text(message, parse_mode='Markdown')

async def show_bot_status(query, context, bot_id, user_id):
    """Show detailed bot status"""
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != user_id:
        await query.answer(f"{E['cross']} Access denied")
        return
    
    status_info = process_manager.get_bot_status(bot_id, bot['process_id'] or 0)
    
    status_text = f"""
{E['chart']} **Bot Status Report**

{E['robot']} **Bot:** {bot['bot_name']}
{E['file']} **File:** `{bot['file_name']}`

{E['info']} **Current Status:**
├ Status: {'🟢 Running' if status_info.get('running') else '🔴 Stopped'}
├ PID: {bot['process_id'] or 'N/A'}
└ Created: {bot['created_date'][:16]}

{'**📊 Performance:**' if status_info.get('running') else ''}
{'├ CPU: ' + str(round(status_info.get('cpu_percent', 0), 2)) + '%' if status_info.get('running') else ''}
{'└ Memory: ' + str(round(status_info.get('memory_mb', 0), 2)) + 'MB' if status_info.get('running') else ''}
    """
    
    await query.answer()
    await query.message.reply_text(status_text, parse_mode='Markdown')

async def show_bot_logs(query, context, bot_id, user_id):
    """Show bot logs"""
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != user_id:
        await query.answer(f"{E['cross']} Access denied")
        return
    
    logs = process_manager.get_bot_logs(bot_id)
    
    logs_text = f"""
{E['file']} **Bot Logs**

{E['robot']} **Bot:** {bot['bot_name']}

{logs}

{E['info']} Use /bot_status for real-time status
    """
    
    await query.answer()
    await query.message.reply_text(logs_text, parse_mode='Markdown')

async def delete_bot(query, context, bot_id, user_id):
    """Delete bot"""
    bot = db.get_bot(bot_id)
    
    if not bot or bot['user_id'] != user_id:
        await query.answer(f"{E['cross']} Access denied")
        return
    
    # Stop if running
    if bot['status'] == 'running':
        process_manager.stop_bot(bot_id, bot['process_id'])
    
    # Delete file
    try:
        if os.path.exists(bot['file_path']):
            os.remove(bot['file_path'])
    except:
        pass
    
    # Delete from database
    db.delete_bot(bot_id)
    
    await query.answer(f"✅ Bot deleted successfully!")
    await query.message.reply_text(
        f"{E['check']} **Bot Deleted**\n\n"
        f"Bot '{bot['bot_name']}' has been removed.",
        parse_mode='Markdown'
    )
