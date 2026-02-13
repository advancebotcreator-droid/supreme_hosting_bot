"""
Supreme Hosting Bot - Configuration
Owner: @shuvohassan00
Channel: GADGET PREMIUM ZONE
"""

import os

# ─────────────────────────────────────────────
#  Bot Configuration
# ─────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8138779207:AAFb9gDpKcgP3vbalCYHEin8b-vZQydSvqo")

# Owner Telegram ID (STRICT - only this user has full control)
OWNER_ID = int(os.getenv("OWNER_ID", "7857957075"))  # Replace with actual owner ID

# Branding
BOT_NAME = "Gadget Premium Host"
CHANNEL_NAME = "GADGET PREMIUM ZONE"
PRIVATE_CHANNEL = "https://t.me/+HSqmdVuHFr84MzRl"
PUBLIC_CHANNEL = "https://t.me/gadgetpremiumzone"
PUBLIC_CHANNEL_USERNAME = "@gadgetpremiumzone"
OWNER_USERNAME = "@shuvohassan00"

# Database
DATABASE_PATH = "data/supreme_hosting.db"

# File storage
UPLOAD_DIR = "data/user_bots"
LOGS_DIR = "data/logs"

# Limits
MAX_FILE_SIZE_MB = 50
MAX_BOTS_FREE = 1
MAX_BOTS_PREMIUM = 10

# Process limits
MAX_LOG_LINES = 50
PROCESS_TIMEOUT = 300  # 5 minutes for free users
PREMIUM_PROCESS_TIMEOUT = 0  # Unlimited for premium

# Supported extensions
SUPPORTED_EXTENSIONS = [".py", ".zip"]
