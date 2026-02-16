from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from database import db
from utils.decorators import track_user, check_banned
from datetime import datetime

E = Config.EMOJI

@track_user
@check_banned
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with beautiful welcome message"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    is_premium = db.is_premium(user.id)
    is_admin = db.is_admin(user.id)
    
    welcome_text = f"""
{E['rocket']} **Welcome to Advanced Bot Hosting Platform!** {E['rocket']}

Hello **{user.first_name}**! {E['party']}

{E['robot']} **What can I do?**
• Host Python (.py) & JavaScript (.js) bots
• Real-time syntax error detection
• Manual module installation
• Process monitoring & logs
• Easy bot management

{E['crown']} **Your Status:**
└ Account: {'Premium' if is_premium else 'Free'} {'💎' if is_premium else ''}
└ Role: {'Admin' if is_admin else 'User'} {'👨‍💼' if is_admin else '👤'}
└ Bots Hosted: {user_data['total_bots'] if user_data else 0}

{E['fire']} **Get Started:**
Use /help to see all available commands!

{E['link']} **Join Our Channels:**
• [Premium Zone]({Config.PRIVATE_CHANNEL})
• [Gadget Box]({Config.PUBLIC_CHANNEL})

━━━━━━━━━━━━━━━━━━━━
Developed by @shuvohassan00
    """
    
    keyboard = [
        [
            InlineKeyboardButton(f"{E['robot']} My Bots", callback_data="my_bots"),
            InlineKeyboardButton(f"{E['upload']} Host Bot", callback_data="host_new_bot")
        ],
        [
            InlineKeyboardButton(f"{E['info']} Help", callback_data="help"),
            InlineKeyboardButton(f"{E['chart']} Stats", callback_data="my_stats")
        ],
        [
            InlineKeyboardButton(f"{E['crown']} Premium", callback_data="premium_info"),
            InlineKeyboardButton(f"{E['link']} Channels", callback_data="channels")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    
    # Notify owner about new user
    if not user_data:
        await notify_owner_new_user(context, user)

async def notify_owner_new_user(context: ContextTypes.DEFAULT_TYPE, user):
    """Notify owner when a new user joins"""
    notification = f"""
{E['bell']} **New User Joined!**

{E['user']} **User Details:**
├ ID: `{user.id}`
├ Name: {user.first_name} {user.last_name or ''}
├ Username: @{user.username or 'No username'}
└ Join Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total Users: {len(db.get_all_users())}
    """
    
    try:
        await context.bot.send_message(
            chat_id=Config.OWNER_ID,
            text=notification,
            parse_mode='Markdown'
        )
    except:
        pass

@track_user
@check_banned
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    
    help_text = f"""
{E['info']} **Command List & Guide** {E['info']}

{E['robot']} **Bot Management:**
├ /mybots - View your hosted bots
├ /start_bot - Start a bot
├ /stop_bot - Stop a running bot
├ /restart_bot - Restart a bot
├ /delete_bot - Delete a bot
├ /bot_status - Check bot status
└ /bot_logs - View bot logs

{E['upload']} **Hosting:**
├ /host - Upload & host a new bot
├ Send .py or .js file directly
└ Send .zip archive with multiple files

{E['package']} **Module Management:**
├ /install <module_name> - Install Python module
└ /installed_modules - View installed modules

{E['user']} **Account:**
├ /profile - View your profile
├ /stats - Your statistics
└ /premium - Premium benefits

{E['settings']} **Settings:**
├ /settings - Bot settings
└ /help - Show this help

{E['admin']} **Admin Commands:** (Admin Only)
├ /admin - Admin panel
├ /addadmin - Add admin
├ /removeadmin - Remove admin
├ /addpremium - Grant premium
├ /removepremium - Remove premium
├ /ban - Ban user
├ /unban - Unban user
├ /broadcast - Send message to all
└ /stats_admin - Global statistics

━━━━━━━━━━━━━━━━━━━━
{E['fire']} **How to Host a Bot:**

1. Prepare your bot code (.py or .js)
2. Send the file to this bot
3. Bot will validate the code
4. If valid, bot will be hosted
5. Use /start_bot to run it!

{E['diamond']} **Premium Features:**
• Host up to 10 bots
• 50MB file size limit
• Priority support
• Advanced monitoring

Need help? Contact @shuvohassan00
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

@track_user
@check_banned
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile"""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    user_bots = db.get_user_bots(user_id)
    
    is_premium = db.is_premium(user_id)
    is_admin = db.is_admin(user_id)
    
    # Calculate active bots
    active_bots = sum(1 for bot in user_bots if bot['status'] == 'running')
    
    premium_text = ""
    if is_premium and user_data['premium_until']:
        premium_until = datetime.fromisoformat(user_data['premium_until'])
        days_left = (premium_until - datetime.now()).days
        premium_text = f"\n├ Premium Until: {premium_until.strftime('%Y-%m-%d')}\n└ Days Left: {days_left} days"
    
    profile_text = f"""
{E['user']} **Your Profile** {E['user']}

{E['info']} **Account Information:**
├ User ID: `{user_id}`
├ Username: @{update.effective_user.username or 'Not set'}
├ Name: {user_data['first_name']} {user_data['last_name'] or ''}
├ Status: {'Premium 💎' if is_premium else 'Free'}
├ Role: {'Admin 👨‍💼' if is_admin else 'User 👤'}
└ Joined: {datetime.fromisoformat(user_data['joined_date']).strftime('%Y-%m-%d')}{premium_text}

{E['chart']} **Statistics:**
├ Total Bots: {user_data['total_bots']}
├ Active Bots: {active_bots}
├ Total Uploads: {user_data['total_uploads']}
└ Last Active: {datetime.fromisoformat(user_data['last_active']).strftime('%Y-%m-%d %H:%M')}

{E['package']} **Limits:**
├ Max Bots: {Config.MAX_BOTS_PREMIUM if is_premium else Config.MAX_BOTS_FREE}
└ Max File Size: {(Config.MAX_FILE_SIZE_PREMIUM if is_premium else Config.MAX_FILE_SIZE_FREE) // (1024*1024)}MB

━━━━━━━━━━━━━━━━━━━━
    """
    
    keyboard = [
        [
            InlineKeyboardButton(f"{E['robot']} My Bots", callback_data="my_bots"),
            InlineKeyboardButton(f"{E['upload']} Host Bot", callback_data="host_new_bot")
        ]
    ]
    
    if not is_premium:
        keyboard.append([
            InlineKeyboardButton(f"{E['crown']} Get Premium", callback_data="premium_info")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        profile_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

@track_user
@check_banned  
async def premium_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium information"""
    
    is_premium = db.is_premium(update.effective_user.id)
    
    premium_text = f"""
{E['crown']} **Premium Membership** {E['diamond']}

{'✅ You are a Premium Member!' if is_premium else '🔓 Unlock Premium Features!'}

{E['fire']} **Premium Benefits:**

{E['check']} Host up to **10 bots** (vs 2 for free)
{E['check']} **50MB** file size limit (vs 5MB)
{E['check']} Priority processing
{E['check']} Advanced bot monitoring
{E['check']} Custom bot names
{E['check']} Detailed analytics
{E['check']} Priority support
{E['check']} No ads or limits

{E['money']} **Pricing:**
├ 1 Month - $5
├ 3 Months - $12
├ 6 Months - $20
└ 1 Year - $35

{E['gift']} **How to Get Premium:**
Contact the owner: @shuvohassan00

━━━━━━━━━━━━━━━━━━━━
    """
    
    keyboard = [[
        InlineKeyboardButton(f"{E['user']} Contact Owner", url="https://t.me/shuvohassan00")
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        premium_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "help":
        await help_command(update, context)
    elif data == "my_bots":
        # This will be handled in hosting_handlers.py
        pass
    elif data == "premium_info":
        await premium_info_command(update, context)
    elif data == "my_stats":
        await profile_command(update, context)
    elif data == "channels":
        channels_text = f"""
{E['link']} **Our Official Channels**

{E['crown']} **Premium Zone:**
└ Join: {Config.PRIVATE_CHANNEL}

{E['fire']} **Gadget Box:**
└ Join: {Config.PUBLIC_CHANNEL}

Stay updated with latest features & updates!
        """
        await query.edit_message_text(channels_text, parse_mode='Markdown')
