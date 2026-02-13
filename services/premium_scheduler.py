"""
Supreme Hosting Bot - Premium Auto-Expiry Scheduler
"""

import asyncio
import logging
from datetime import datetime

from database import db

logger = logging.getLogger(__name__)


class PremiumScheduler:
    """Handles automatic premium expiration checks."""
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self._task: asyncio.Task = None
        self._running = False

    def set_bot(self, bot_instance):
        self.bot = bot_instance

    async def start(self):
        """Start the scheduler loop."""
        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info("⏰ Premium scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("⏰ Premium scheduler stopped")

    async def _check_loop(self):
        """Main loop - checks every 60 seconds for expired premiums."""
        while self._running:
            try:
                await self._check_expired()
            except Exception as e:
                logger.error(f"Premium check error: {e}")
            
            await asyncio.sleep(60)  # Check every minute

    async def _check_expired(self):
        """Check and handle expired premium users."""
        from utils.texts import Texts
        
        expired_users = await db.get_expired_premiums()
        
        for user in expired_users:
            user_id = user['user_id']
            
            # Revoke premium
            await db.revoke_premium(user_id)
            await db.log_activity(user_id, "premium_expired", "Auto-expired by scheduler")
            
            # Notify user
            if self.bot:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=Texts.premium_expired(),
                        parse_mode="HTML"
                    )
                    logger.info(f"Premium expired for user {user_id}, notification sent")
                except Exception as e:
                    logger.warning(f"Failed to notify user {user_id} about premium expiry: {e}")


# Global scheduler instance
premium_scheduler = PremiumScheduler()
