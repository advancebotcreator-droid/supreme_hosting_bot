"""
Supreme Hosting Bot - All Formatted Text Messages
Premium look with emojis and formatting
"""

from datetime import datetime, timedelta
from config import (
    BOT_NAME, CHANNEL_NAME, PRIVATE_CHANNEL, PUBLIC_CHANNEL,
    PUBLIC_CHANNEL_USERNAME, OWNER_USERNAME, MAX_BOTS_FREE, MAX_BOTS_PREMIUM
)


class Texts:
    
    @staticmethod
    def welcome(full_name: str, user_id: int) -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   🌟 <b>{BOT_NAME}</b> 🌟\n"
            f"╚══════════════════════════╝\n\n"
            f"👋 <b>Welcome, {full_name}!</b>\n\n"
            f"🤖 <i>I am the most advanced Telegram Bot Hosting solution. "
            f"Upload your Python scripts and I'll keep them running 24/7 on our VPS!</i>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>What I Can Do:</b>\n"
            f"  ├ 📤 <b>Upload</b> .py files or .zip archives\n"
            f"  ├ 🔍 <b>Syntax Check</b> before deployment\n"
            f"  ├ ▶️ <b>Start/Stop/Restart</b> your bots\n"
            f"  ├ 📋 <b>View Live Logs</b>\n"
            f"  ├ 📦 <b>Install Dependencies</b>\n"
            f"  └ 👑 <b>Premium Features</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆓 <b>Free:</b> {MAX_BOTS_FREE} bot  |  "
            f"👑 <b>Premium:</b> {MAX_BOTS_PREMIUM} bots\n\n"
            f"📢 <b>Channel:</b> {PUBLIC_CHANNEL_USERNAME}\n"
            f"👨‍💻 <b>Developer:</b> {OWNER_USERNAME}\n\n"
            f"<i>🔽 Use the buttons below to get started!</i>"
        )

    @staticmethod
    def help_text() -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   📖 <b>Help & Commands</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"<b>📋 User Commands:</b>\n"
            f"  /start - Start the bot\n"
            f"  /help - Show this help\n"
            f"  /mybots - List your hosted bots\n"
            f"  /upload - Upload a new bot file\n"
            f"  /install &lt;module&gt; - Install a Python module\n"
            f"  /profile - View your profile\n"
            f"  /logs &lt;bot_id&gt; - View bot logs\n\n"
            f"<b>👑 Admin Commands:</b>\n"
            f"  /addpremium @user 30d - Grant premium\n"
            f"  /removepremium @user - Revoke premium\n"
            f"  /ban @user - Ban a user\n"
            f"  /unban @user - Unban a user\n"
            f"  /broadcast &lt;message&gt; - Send to all users\n\n"
            f"<b>🔐 Owner Commands:</b>\n"
            f"  /addadmin @user - Add admin\n"
            f"  /removeadmin @user - Remove admin\n"
            f"  /stats - Bot statistics\n"
            f"  /setgroup - Set admin group\n"
            f"  /allusers - List all users\n"
            f"  /allbots - List all hosted bots\n"
            f"  /killall - Stop all running bots\n\n"
            f"<b>📤 How to Upload:</b>\n"
            f"  1️⃣ Send a <code>.py</code> file or <code>.zip</code> archive\n"
            f"  2️⃣ Bot checks syntax automatically\n"
            f"  3️⃣ If valid, it gets saved\n"
            f"  4️⃣ Use /mybots to manage it\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 {PUBLIC_CHANNEL_USERNAME} | 👨‍💻 {OWNER_USERNAME}"
        )

    @staticmethod
    def profile(user: dict, bot_count: int) -> str:
        premium_status = "👑 Premium" if user['is_premium'] else "🆓 Free"
        admin_status = "✅ Admin" if user['is_admin'] else "❌ No"
        
        premium_expiry = "N/A"
        if user['is_premium'] and user['premium_expires_at'] > 0:
            exp = datetime.fromtimestamp(user['premium_expires_at'])
            remaining = exp - datetime.now()
            if remaining.total_seconds() > 0:
                days = remaining.days
                hours = remaining.seconds // 3600
                premium_expiry = f"{days}d {hours}h remaining"
            else:
                premium_expiry = "⚠️ Expiring..."

        created = datetime.fromtimestamp(user['created_at']).strftime("%Y-%m-%d %H:%M")
        
        max_bots = user.get('max_bots', MAX_BOTS_FREE)
        
        return (
            f"╔══════════════════════════╗\n"
            f"   👤 <b>Your Profile</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"  🆔 <b>User ID:</b> <code>{user['user_id']}</code>\n"
            f"  👤 <b>Name:</b> {user['full_name']}\n"
            f"  📛 <b>Username:</b> @{user['username'] or 'N/A'}\n\n"
            f"  ━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  🏷️ <b>Status:</b> {premium_status}\n"
            f"  🛡️ <b>Admin:</b> {admin_status}\n"
            f"  ⏳ <b>Premium Expires:</b> {premium_expiry}\n\n"
            f"  ━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  🤖 <b>Hosted Bots:</b> {bot_count}/{max_bots}\n"
            f"  📅 <b>Joined:</b> {created}\n\n"
            f"  📢 <b>Channel:</b> {PUBLIC_CHANNEL_USERNAME}\n"
        )

    @staticmethod
    def upload_prompt() -> str:
        return (
            f"📤 <b>Upload Your Bot</b>\n\n"
            f"Send me a file to host:\n\n"
            f"  ✅ <code>.py</code> — Python script\n"
            f"  ✅ <code>.zip</code> — Archive (must contain a main .py file)\n\n"
            f"⚡ <b>Important:</b>\n"
            f"  • Max file size: 50MB\n"
            f"  • Syntax will be auto-checked\n"
            f"  • Include <code>requirements.txt</code> in .zip for auto-install\n\n"
            f"<i>📎 Just send the file as a document...</i>"
        )

    @staticmethod
    def syntax_error(filename: str, error_msg: str, line_no: int = 0) -> str:
        line_info = f" (Line {line_no})" if line_no else ""
        return (
            f"╔══════════════════════════╗\n"
            f"   ❌ <b>SYNTAX ERROR</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"📄 <b>File:</b> <code>{filename}</code>{line_info}\n\n"
            f"🔴 <b>Error Details:</b>\n"
            f"<pre>{error_msg}</pre>\n\n"
            f"⚠️ <b>File REJECTED!</b> Please fix the error and re-upload.\n\n"
            f"<i>💡 Tip: Test your code locally before uploading.</i>"
        )

    @staticmethod
    def syntax_ok(filename: str) -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   ✅ <b>SYNTAX CHECK PASSED</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"📄 <b>File:</b> <code>{filename}</code>\n"
            f"🔍 <b>Status:</b> No syntax errors found!\n\n"
            f"⏳ <i>Saving and deploying...</i>"
        )

    @staticmethod
    def bot_saved(bot_id: int, filename: str) -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   🎉 <b>BOT DEPLOYED!</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"📄 <b>File:</b> <code>{filename}</code>\n"
            f"🆔 <b>Bot ID:</b> <code>{bot_id}</code>\n"
            f"📊 <b>Status:</b> 🔴 Stopped\n\n"
            f"Use /mybots to manage your bots.\n"
            f"Press ▶️ <b>Start</b> to run it!\n\n"
            f"<i>⚡ Powered by {BOT_NAME}</i>"
        )

    @staticmethod
    def my_bots_header(count: int) -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   🤖 <b>Your Hosted Bots</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"📊 <b>Total Bots:</b> {count}\n\n"
        )

    @staticmethod
    def bot_info(bot: dict) -> str:
        status_emoji = "🟢" if bot['status'] == 'running' else "🔴"
        status_text = bot['status'].upper()
        created = datetime.fromtimestamp(bot['created_at']).strftime("%Y-%m-%d %H:%M")
        
        return (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Bot ID:</b> <code>{bot['bot_id']}</code>\n"
            f"📄 <b>File:</b> <code>{bot['original_name']}</code>\n"
            f"{status_emoji} <b>Status:</b> {status_text}\n"
            f"📅 <b>Deployed:</b> {created}\n"
        )

    @staticmethod
    def no_bots() -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   🤖 <b>Your Hosted Bots</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"📭 <b>No bots deployed yet!</b>\n\n"
            f"📤 Send a <code>.py</code> or <code>.zip</code> file to get started.\n\n"
            f"<i>💡 Tip: Use /upload for instructions.</i>"
        )

    @staticmethod
    def bot_started(bot_id: int, filename: str) -> str:
        return (
            f"▶️ <b>Bot Started Successfully!</b>\n\n"
            f"🆔 <b>Bot ID:</b> <code>{bot_id}</code>\n"
            f"📄 <b>File:</b> <code>{filename}</code>\n"
            f"🟢 <b>Status:</b> RUNNING\n\n"
            f"<i>📋 Use 'Logs' to monitor output.</i>"
        )

    @staticmethod
    def bot_stopped(bot_id: int, filename: str) -> str:
        return (
            f"⏹️ <b>Bot Stopped!</b>\n\n"
            f"🆔 <b>Bot ID:</b> <code>{bot_id}</code>\n"
            f"📄 <b>File:</b> <code>{filename}</code>\n"
            f"🔴 <b>Status:</b> STOPPED\n"
        )

    @staticmethod
    def bot_restarted(bot_id: int, filename: str) -> str:
        return (
            f"🔄 <b>Bot Restarted!</b>\n\n"
            f"🆔 <b>Bot ID:</b> <code>{bot_id}</code>\n"
            f"📄 <b>File:</b> <code>{filename}</code>\n"
            f"🟢 <b>Status:</b> RUNNING\n"
        )

    @staticmethod
    def logs_header(bot_id: int, filename: str) -> str:
        return (
            f"📋 <b>Logs for Bot #{bot_id}</b>\n"
            f"📄 <code>{filename}</code>\n\n"
        )

    @staticmethod
    def no_logs() -> str:
        return "<i>📭 No logs available yet.</i>"

    @staticmethod
    def premium_granted(days: int, admin_name: str) -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   👑 <b>PREMIUM ACTIVATED!</b> 👑\n"
            f"╚══════════════════════════╝\n\n"
            f"🎉 <b>Congratulations!</b>\n\n"
            f"You have been granted <b>Premium</b> access!\n\n"
            f"  ⏳ <b>Duration:</b> {days} days\n"
            f"  🤖 <b>Max Bots:</b> {MAX_BOTS_PREMIUM}\n"
            f"  👤 <b>Granted by:</b> {admin_name}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  🌟 <b>Premium Benefits:</b>\n"
            f"  ├ 🤖 Up to {MAX_BOTS_PREMIUM} hosted bots\n"
            f"  ├ ⏰ Unlimited runtime\n"
            f"  ├ 🚀 Priority support\n"
            f"  └ 📦 Unlimited dependencies\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<i>Thank you for choosing {BOT_NAME}! 🌟</i>\n"
            f"📢 {PUBLIC_CHANNEL_USERNAME}"
        )

    @staticmethod
    def premium_expired() -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   ⏰ <b>PREMIUM EXPIRED</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"😔 Your <b>Premium</b> subscription has expired.\n\n"
            f"  🤖 <b>Max Bots:</b> Reduced to {MAX_BOTS_FREE}\n"
            f"  ⏰ <b>Runtime:</b> Limited\n\n"
            f"💡 <b>Contact an admin to renew!</b>\n\n"
            f"  👨‍💻 {OWNER_USERNAME}\n"
            f"  📢 {PUBLIC_CHANNEL_USERNAME}\n\n"
            f"<i>We hope to see you back soon! 🌟</i>"
        )

    @staticmethod
    def admin_granted(owner_name: str) -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   🛡️ <b>ADMIN ACCESS GRANTED!</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"🎉 You are now an <b>Admin</b> of {BOT_NAME}!\n\n"
            f"  👤 <b>Granted by:</b> {owner_name}\n\n"
            f"<b>🔧 Your Powers:</b>\n"
            f"  ├ 👑 Manage Premium users\n"
            f"  ├ 🚫 Ban/Unban users\n"
            f"  ├ 📢 Broadcast messages\n"
            f"  └ 📊 View statistics\n\n"
            f"<i>Use your powers responsibly! 🛡️</i>"
        )

    @staticmethod
    def admin_removed() -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   ⚠️ <b>ADMIN ACCESS REVOKED</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"Your admin privileges have been removed.\n\n"
            f"<i>Contact {OWNER_USERNAME} for questions.</i>"
        )

    @staticmethod
    def stats(total_users: int, premium_users: int, admin_count: int,
              total_bots: int, running_bots: int) -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   📊 <b>BOT STATISTICS</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"  👥 <b>Total Users:</b> {total_users}\n"
            f"  👑 <b>Premium Users:</b> {premium_users}\n"
            f"  🛡️ <b>Admins:</b> {admin_count}\n\n"
            f"  ━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  🤖 <b>Total Bots:</b> {total_bots}\n"
            f"  🟢 <b>Running Bots:</b> {running_bots}\n"
            f"  🔴 <b>Stopped Bots:</b> {total_bots - running_bots}\n\n"
            f"  ━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  📢 <b>Channel:</b> {PUBLIC_CHANNEL_USERNAME}\n"
            f"  👨‍💻 <b>Owner:</b> {OWNER_USERNAME}\n"
        )

    @staticmethod
    def file_forwarded_to_owner(user_id: int, username: str, full_name: str,
                                 filename: str) -> str:
        return (
            f"╔══════════════════════════╗\n"
            f"   📥 <b>NEW FILE UPLOAD</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"  👤 <b>User:</b> {full_name}\n"
            f"  📛 <b>Username:</b> @{username or 'N/A'}\n"
            f"  🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            f"  📄 <b>File:</b> <code>{filename}</code>\n"
            f"  📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

    @staticmethod
    def install_success(module: str) -> str:
        return (
            f"✅ <b>Module Installed!</b>\n\n"
            f"📦 <code>{module}</code> has been installed successfully.\n"
        )

    @staticmethod
    def install_failed(module: str, error: str) -> str:
        return (
            f"❌ <b>Installation Failed!</b>\n\n"
            f"📦 <code>{module}</code>\n\n"
            f"<b>Error:</b>\n<pre>{error[:1000]}</pre>\n"
        )

    @staticmethod
    def banned_msg() -> str:
        return (
            f"🚫 <b>Access Denied!</b>\n\n"
            f"You have been banned from using this bot.\n"
            f"Contact {OWNER_USERNAME} if you think this is a mistake."
        )

    @staticmethod
    def not_authorized() -> str:
        return (
            f"🔒 <b>Unauthorized!</b>\n\n"
            f"You don't have permission for this action."
        )

    @staticmethod
    def bot_limit_reached(current: int, max_bots: int) -> str:
        return (
            f"⚠️ <b>Bot Limit Reached!</b>\n\n"
            f"You have <b>{current}/{max_bots}</b> bots deployed.\n\n"
            f"💡 <b>Upgrade to Premium</b> for up to {MAX_BOTS_PREMIUM} bots!\n"
            f"Contact {OWNER_USERNAME} or an admin."
        )

    @staticmethod
    def bot_deleted(bot_id: int) -> str:
        return (
            f"🗑️ <b>Bot Deleted!</b>\n\n"
            f"Bot <code>#{bot_id}</code> has been permanently removed.\n"
        )

    @staticmethod
    def requirements_installing() -> str:
        return "📦 <i>Installing requirements.txt...</i>"

    @staticmethod
    def requirements_done() -> str:
        return "✅ <b>Requirements installed successfully!</b>"

    @staticmethod
    def requirements_failed(error: str) -> str:
        return f"⚠️ <b>Some requirements failed:</b>\n<pre>{error[:800]}</pre>"
