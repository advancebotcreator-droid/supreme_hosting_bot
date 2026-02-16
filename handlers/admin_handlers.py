from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from database import db
from utils.decorators import admin_only, owner_only
from datetime import datetime

E = Config.EMOJI

@admin_only
async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    
    stats = db.get_statistics()
    
    admin_text = f"""
{E['admin']} **Admin Control Panel** {E['shield']}

{E['chart']} **Statistics:**
├ Total Users: {stats['total_users']}
├ Premium Users: {stats['premium_users']}
├ Total Bots: {stats['total_bots']}
├ Active Bots: {stats['active_bots']}
└ Total Uploads: {stats['total_uploads']}

{E['gear']} **Admin Commands:**

**User Management:**
├ /addadmin <user_id> - Grant admin
├ /removeadmin <user_id> - Remove admin
├ /adminlist - View all admins
├ /ban <user_id> - Ban user
├ /unban <user_id> - Unban user
└ /userinfo <user_id> - User details

**Premium Management:**
├ /addpremium <user_id> <days> - Grant premium
├ /removepremium <user_id> - Remove premium
└ /premiumlist - View premium users

**Broadcast:**
├ /broadcast <message> - Send to all users
└ /broadcast_premium <message> - Send to premium

**Statistics:**
└ /stats_admin - Detailed statistics

━━━━━━━━━━━━━━━━━━━━
    """
    
    keyboard = [
        [
            InlineKeyboardButton(f"{E['users']} Users ({stats['total_users']})", callback_data="admin_users"),
            InlineKeyboardButton(f"{E['crown']} Premium ({stats['premium_users']})", callback_data="admin_premium")
        ],
        [
            InlineKeyboardButton(f"{E['admin']} Admins", callback_data="admin_list"),
            InlineKeyboardButton(f"{E['chart']} Stats", callback_data="admin_stats")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(admin_text, parse_mode='Markdown', reply_markup=reply_markup)

@admin_only
async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add admin"""
    if not context.args:
        await update.message.reply_text(
            f"{E['info']} **Usage:** `/addadmin <user_id>`\n\n"
            f"Example: `/addadmin 123456789`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(f"{E['cross']} Invalid user ID!", parse_mode='Markdown')
        return
    
    # Check if user exists
    user = db.get_user(target_user_id)
    if not user:
        await update.message.reply_text(
            f"{E['cross']} User not found!\n\n"
            f"User must start the bot first.",
            parse_mode='Markdown'
        )
        return
    
    # Check if already admin
    if db.is_admin(target_user_id):
        await update.message.reply_text(
            f"{E['info']} User is already an admin!",
            parse_mode='Markdown'
        )
        return
    
    # Add admin
    db.add_admin(target_user_id)
    
    # Log action
    db.add_admin_log(
        admin_id=update.effective_user.id,
        action_type='add_admin',
        target_user_id=target_user_id,
        details=f"Added admin: {user['first_name']}"
    )
    
    success_text = f"""
{E['check']} **Admin Added Successfully!**

{E['user']} **User Details:**
├ ID: `{target_user_id}`
├ Name: {user['first_name']} {user['last_name'] or ''}
└ Username: @{user['username'] or 'No username'}

{E['admin']} User is now an administrator!
    """
    
    await update.message.reply_text(success_text, parse_mode='Markdown')
    
    # Notify admin group
    try:
        await context.bot.send_message(
            chat_id=Config.ADMIN_GROUP_ID,
            text=f"{E['bell']} **New Admin Added!**\n\n"
                 f"User: {user['first_name']} (@{user['username'] or target_user_id})\n"
                 f"By: {update.effective_user.first_name}",
            parse_mode='Markdown'
        )
    except:
        pass
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"{E['party']} **Congratulations!** {E['party']}\n\n"
                 f"You have been promoted to **Administrator**!\n\n"
                 f"Use /admin to access the admin panel.",
            parse_mode='Markdown'
        )
    except:
        pass

@admin_only
async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove admin"""
    if not context.args:
        await update.message.reply_text(
            f"{E['info']} **Usage:** `/removeadmin <user_id>`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(f"{E['cross']} Invalid user ID!", parse_mode='Markdown')
        return
    
    # Can't remove owner
    if target_user_id == Config.OWNER_ID:
        await update.message.reply_text(
            f"{E['cross']} Cannot remove the owner!",
            parse_mode='Markdown'
        )
        return
    
    # Check if admin
    if not db.is_admin(target_user_id):
        await update.message.reply_text(
            f"{E['info']} User is not an admin!",
            parse_mode='Markdown'
        )
        return
    
    # Remove admin
    db.remove_admin(target_user_id)
    
    user = db.get_user(target_user_id)
    
    # Log action
    db.add_admin_log(
        admin_id=update.effective_user.id,
        action_type='remove_admin',
        target_user_id=target_user_id,
        details=f"Removed admin: {user['first_name']}"
    )
    
    await update.message.reply_text(
        f"{E['check']} **Admin Removed**\n\n"
        f"User `{target_user_id}` is no longer an administrator.",
        parse_mode='Markdown'
    )
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"{E['info']} You have been removed from administrators.",
            parse_mode='Markdown'
        )
    except:
        pass

@admin_only
async def admin_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin list"""
    admins = db.get_all_admins()
    
    if not admins:
        await update.message.reply_text(
            f"{E['info']} No admins found.",
            parse_mode='Markdown'
        )
        return
    
    admin_text = f"{E['admin']} **Administrator List** ({len(admins)})\n\n"
    
    for i, admin in enumerate(admins, 1):
        admin_text += f"{i}. **{admin['first_name']}** {admin['last_name'] or ''}\n"
        admin_text += f"   ├ ID: `{admin['user_id']}`\n"
        admin_text += f"   ├ Username: @{admin['username'] or 'None'}\n"
        admin_text += f"   └ Since: {admin['joined_date'][:10]}\n\n"
    
    await update.message.reply_text(admin_text, parse_mode='Markdown')

@admin_only
async def add_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add premium to user"""
    if len(context.args) < 2:
        await update.message.reply_text(
            f"{E['info']} **Usage:** `/addpremium <user_id> <days>`\n\n"
            f"Example: `/addpremium 123456789 30`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        days = int(context.args[1])
    except ValueError:
        await update.message.reply_text(
            f"{E['cross']} Invalid parameters!",
            parse_mode='Markdown'
        )
        return
    
    if days < 1 or days > 3650:
        await update.message.reply_text(
            f"{E['cross']} Days must be between 1-3650!",
            parse_mode='Markdown'
        )
        return
    
    # Check if user exists
    user = db.get_user(target_user_id)
    if not user:
        await update.message.reply_text(
            f"{E['cross']} User not found!",
            parse_mode='Markdown'
        )
        return
    
    # Add premium
    db.add_premium(target_user_id, days)
    
    # Log action
    db.add_admin_log(
        admin_id=update.effective_user.id,
        action_type='add_premium',
        target_user_id=target_user_id,
        details=f"Added {days} days premium"
    )
    
    premium_until = db.get_user(target_user_id)['premium_until']
    
    success_text = f"""
{E['check']} **Premium Granted!** {E['diamond']}

{E['user']} **User Details:**
├ ID: `{target_user_id}`
├ Name: {user['first_name']}
└ Username: @{user['username'] or 'None'}

{E['crown']} **Premium Details:**
├ Duration: {days} days
└ Valid Until: {premium_until[:10]}

User notified via DM!
    """
    
    await update.message.reply_text(success_text, parse_mode='Markdown')
    
    # Notify admin group
    try:
        await context.bot.send_message(
            chat_id=Config.ADMIN_GROUP_ID,
            text=f"{E['bell']} **Premium Granted!**\n\n"
                 f"User: {user['first_name']}\n"
                 f"Duration: {days} days\n"
                 f"By: {update.effective_user.first_name}",
            parse_mode='Markdown'
        )
    except:
        pass
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"{E['party']} **Congratulations!** {E['party']}\n\n"
                 f"You have been granted **Premium Membership**!\n\n"
                 f"{E['crown']} **Benefits:**\n"
                 f"• Host up to 10 bots\n"
                 f"• 50MB file size limit\n"
                 f"• Priority support\n\n"
                 f"{E['calendar']} **Duration:** {days} days\n"
                 f"{E['time']} **Valid Until:** {premium_until[:10]}\n\n"
                 f"Enjoy your premium features! {E['fire']}",
            parse_mode='Markdown'
        )
    except:
        pass

@admin_only
async def remove_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove premium from user"""
    if not context.args:
        await update.message.reply_text(
            f"{E['info']} **Usage:** `/removepremium <user_id>`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(f"{E['cross']} Invalid user ID!", parse_mode='Markdown')
        return
    
    # Check if premium
    if not db.is_premium(target_user_id):
        await update.message.reply_text(
            f"{E['info']} User doesn't have premium!",
            parse_mode='Markdown'
        )
        return
    
    # Remove premium
    db.remove_premium(target_user_id)
    
    user = db.get_user(target_user_id)
    
    # Log action
    db.add_admin_log(
        admin_id=update.effective_user.id,
        action_type='remove_premium',
        target_user_id=target_user_id,
        details=f"Removed premium from {user['first_name']}"
    )
    
    await update.message.reply_text(
        f"{E['check']} **Premium Removed**\n\n"
        f"User `{target_user_id}` is now a free user.",
        parse_mode='Markdown'
    )
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"{E['info']} Your premium membership has expired or been removed.\n\n"
                 f"You are now on the free plan.\n\n"
                 f"Contact @shuvohassan00 to renew premium.",
            parse_mode='Markdown'
        )
    except:
        pass

@admin_only
async def premium_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium users list"""
    premium_users = db.get_all_premium_users()
    
    if not premium_users:
        await update.message.reply_text(
            f"{E['info']} No premium users found.",
            parse_mode='Markdown'
        )
        return
    
    premium_text = f"{E['crown']} **Premium Users** ({len(premium_users)})\n\n"
    
    for i, user in enumerate(premium_users, 1):
        premium_until = datetime.fromisoformat(user['premium_until'])
        days_left = (premium_until - datetime.now()).days
        
        premium_text += f"{i}. **{user['first_name']}**\n"
        premium_text += f"   ├ ID: `{user['user_id']}`\n"
        premium_text += f"   ├ Username: @{user['username'] or 'None'}\n"
        premium_text += f"   ├ Valid Until: {user['premium_until'][:10]}\n"
        premium_text += f"   └ Days Left: {days_left}\n\n"
    
    await update.message.reply_text(premium_text, parse_mode='Markdown')

@admin_only
async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user"""
    if not context.args:
        await update.message.reply_text(
            f"{E['info']} **Usage:** `/ban <user_id>`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(f"{E['cross']} Invalid user ID!", parse_mode='Markdown')
        return
    
    # Can't ban owner or admins
    if target_user_id == Config.OWNER_ID or db.is_admin(target_user_id):
        await update.message.reply_text(
            f"{E['cross']} Cannot ban owner or admins!",
            parse_mode='Markdown'
        )
        return
    
    # Ban user
    db.ban_user(target_user_id)
    
    user = db.get_user(target_user_id)
    
    # Log action
    db.add_admin_log(
        admin_id=update.effective_user.id,
        action_type='ban_user',
        target_user_id=target_user_id,
        details=f"Banned user: {user['first_name']}"
    )
    
    await update.message.reply_text(
        f"{E['check']} **User Banned**\n\n"
        f"User `{target_user_id}` has been banned.",
        parse_mode='Markdown'
    )

@admin_only
async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    if not context.args:
        await update.message.reply_text(
            f"{E['info']} **Usage:** `/unban <user_id>`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(f"{E['cross']} Invalid user ID!", parse_mode='Markdown')
        return
    
    # Unban user
    db.unban_user(target_user_id)
    
    user = db.get_user(target_user_id)
    
    # Log action
    db.add_admin_log(
        admin_id=update.effective_user.id,
        action_type='unban_user',
        target_user_id=target_user_id,
        details=f"Unbanned user: {user['first_name']}"
    )
    
    await update.message.reply_text(
        f"{E['check']} **User Unbanned**\n\n"
        f"User `{target_user_id}` can now use the bot.",
        parse_mode='Markdown'
    )

@owner_only
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    if not context.args:
        await update.message.reply_text(
            f"{E['info']} **Usage:** `/broadcast <message>`\n\n"
            f"Example: `/broadcast Hello everyone!`",
            parse_mode='Markdown'
        )
        return
    
    message = ' '.join(context.args)
    all_users = db.get_all_users()
    
    status_msg = await update.message.reply_text(
        f"{E['gear']} **Broadcasting...**\n\n"
        f"Total users: {len(all_users)}",
        parse_mode='Markdown'
    )
    
    success_count = 0
    failed_count = 0
    
    broadcast_text = f"""
{E['bell']} **Broadcast Message**

{message}

━━━━━━━━━━━━━━━━━━━━
From: Bot Administration
    """
    
    for user in all_users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=broadcast_text,
                parse_mode='Markdown'
            )
            success_count += 1
        except:
            failed_count += 1
    
    await status_msg.edit_text(
        f"{E['check']} **Broadcast Complete!**\n\n"
        f"✅ Sent: {success_count}\n"
        f"❌ Failed: {failed_count}\n"
        f"📊 Total: {len(all_users)}",
        parse_mode='Markdown'
    )

@admin_only
async def stats_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics"""
    stats = db.get_statistics()
    all_users = db.get_all_users()
    
    # Calculate additional stats
    active_today = sum(1 for user in all_users 
                       if user['last_active'] and 
                       datetime.fromisoformat(user['last_active']).date() == datetime.now().date())
    
    stats_text = f"""
{E['chart']} **Detailed Statistics Report**

{E['users']} **User Statistics:**
├ Total Users: {stats['total_users']}
├ Premium Users: {stats['premium_users']}
├ Free Users: {stats['total_users'] - stats['premium_users']}
├ Active Today: {active_today}
└ Admins: {len(db.get_all_admins())}

{E['robot']} **Bot Statistics:**
├ Total Bots Hosted: {stats['total_bots']}
├ Currently Running: {stats['active_bots']}
├ Stopped: {stats['total_bots'] - stats['active_bots']}
└ Total Uploads: {stats['total_uploads']}

{E['calendar']} **Report Date:**
└ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')
