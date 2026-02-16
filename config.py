import os
from datetime import datetime

class Config:
    # Bot Configuration
    BOT_TOKEN = "8138779207:AAEc-fA2gQKhy1a4wiMPoihLn1j6xaCeslI"
    OWNER_ID = 7857957075  # @shuvohassan00 এর Telegram ID
    
    # Channels
    PRIVATE_CHANNEL = "@gadgetpremiumzone"  # Private channel username
    PUBLIC_CHANNEL = "@gadgetpremiumzone"   # Public channel username
    
    # Admin Group (notifications পাঠানোর জন্য)
    ADMIN_GROUP_ID = 7857957075  # Your admin group ID
    
    # Database
    DATABASE_PATH = "data/users.db"
    
    # File Limits
    MAX_FILE_SIZE_FREE = 5 * 1024 * 1024      # 5MB for free users
    MAX_FILE_SIZE_PREMIUM = 50 * 1024 * 1024  # 50MB for premium users
    MAX_BOTS_FREE = 2
    MAX_BOTS_PREMIUM = 10
    
    # Paths
    HOSTED_BOTS_DIR = "data/hosted_bots"
    
    # Emojis for beautiful design
    EMOJI = {
        'robot': '🤖',
        'fire': '🔥',
        'check': '✅',
        'cross': '❌',
        'warning': '⚠️',
        'rocket': '🚀',
        'gear': '⚙️',
        'folder': '📁',
        'file': '📄',
        'package': '📦',
        'chart': '📊',
        'crown': '👑',
        'key': '🔑',
        'shield': '🛡️',
        'star': '⭐',
        'diamond': '💎',
        'lightning': '⚡',
        'party': '🎉',
        'bell': '🔔',
        'link': '🔗',
        'user': '👤',
        'users': '👥',
        'admin': '👨‍💼',
        'time': '⏰',
        'calendar': '📅',
        'upload': '📤',
        'download': '📥',
        'play': '▶️',
        'stop': '⏹️',
        'restart': '🔄',
        'delete': '🗑️',
        'edit': '✏️',
        'search': '🔍',
        'settings': '⚙️',
        'info': 'ℹ️',
        'money': '💰',
        'gift': '🎁'
    }
    
    # Create directories
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    os.makedirs(HOSTED_BOTS_DIR, exist_ok=True)
