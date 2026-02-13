"""
Supreme Hosting Bot - Database Layer
Async SQLite with full schema management
"""

import aiosqlite
import os
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from config import DATABASE_PATH


class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")
        await self._create_tables()

    async def close(self):
        if self._connection:
            await self._connection.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._connection:
            raise RuntimeError("Database not connected")
        return self._connection

    async def _create_tables(self):
        await self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_expires_at REAL DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                max_bots INTEGER DEFAULT 1,
                created_at REAL DEFAULT 0,
                updated_at REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS hosted_bots (
                bot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                original_name TEXT NOT NULL,
                language TEXT DEFAULT 'python',
                status TEXT DEFAULT 'stopped',
                pid INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0,
                started_at REAL DEFAULT 0,
                stopped_at REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS bot_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                log_type TEXT DEFAULT 'stdout',
                message TEXT,
                created_at REAL DEFAULT 0,
                FOREIGN KEY (bot_id) REFERENCES hosted_bots(bot_id)
            );

            CREATE TABLE IF NOT EXISTS admin_group (
                group_id INTEGER PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                created_at REAL DEFAULT 0
            );
        """)
        await self.conn.commit()

    # ─────────────── User Operations ───────────────
    async def get_user(self, user_id: int) -> Optional[Dict]:
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def create_user(self, user_id: int, username: str, full_name: str):
        now = time.time()
        await self.conn.execute(
            """INSERT OR IGNORE INTO users 
               (user_id, username, full_name, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, username, full_name, now, now)
        )
        await self.conn.execute(
            """UPDATE users SET username = ?, full_name = ?, updated_at = ?
               WHERE user_id = ?""",
            (username, full_name, now, user_id)
        )
        await self.conn.commit()

    async def set_premium(self, user_id: int, days: int):
        now = time.time()
        expires = now + (days * 86400)
        await self.conn.execute(
            """UPDATE users SET is_premium = 1, premium_expires_at = ?,
               max_bots = ?, updated_at = ? WHERE user_id = ?""",
            (expires, 10, now, user_id)
        )
        await self.conn.commit()

    async def revoke_premium(self, user_id: int):
        now = time.time()
        await self.conn.execute(
            """UPDATE users SET is_premium = 0, premium_expires_at = 0,
               max_bots = 1, updated_at = ? WHERE user_id = ?""",
            (now, user_id)
        )
        await self.conn.commit()

    async def set_admin(self, user_id: int, is_admin: bool):
        now = time.time()
        await self.conn.execute(
            "UPDATE users SET is_admin = ?, updated_at = ? WHERE user_id = ?",
            (1 if is_admin else 0, now, user_id)
        )
        await self.conn.commit()

    async def set_banned(self, user_id: int, is_banned: bool):
        now = time.time()
        await self.conn.execute(
            "UPDATE users SET is_banned = ?, updated_at = ? WHERE user_id = ?",
            (1 if is_banned else 0, now, user_id)
        )
        await self.conn.commit()

    async def get_all_admins(self) -> List[Dict]:
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE is_admin = 1"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_expired_premiums(self) -> List[Dict]:
        now = time.time()
        cursor = await self.conn.execute(
            """SELECT * FROM users WHERE is_premium = 1 
               AND premium_expires_at > 0 AND premium_expires_at <= ?""",
            (now,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_all_users(self) -> List[Dict]:
        cursor = await self.conn.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_premium_users(self) -> List[Dict]:
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE is_premium = 1"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_user_count(self) -> int:
        cursor = await self.conn.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0]

    # ─────────────── Bot Operations ───────────────
    async def create_bot(self, user_id: int, file_name: str, file_path: str,
                         original_name: str, language: str = "python") -> int:
        now = time.time()
        cursor = await self.conn.execute(
            """INSERT INTO hosted_bots 
               (user_id, file_name, file_path, original_name, language, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'stopped', ?)""",
            (user_id, file_name, file_path, original_name, language, now)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_bot(self, bot_id: int) -> Optional[Dict]:
        cursor = await self.conn.execute(
            "SELECT * FROM hosted_bots WHERE bot_id = ?", (bot_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_bots(self, user_id: int) -> List[Dict]:
        cursor = await self.conn.execute(
            "SELECT * FROM hosted_bots WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_user_bot_count(self, user_id: int) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) FROM hosted_bots WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0]

    async def update_bot_status(self, bot_id: int, status: str, pid: int = 0):
        now = time.time()
        if status == "running":
            await self.conn.execute(
                "UPDATE hosted_bots SET status = ?, pid = ?, started_at = ? WHERE bot_id = ?",
                (status, pid, now, bot_id)
            )
        else:
            await self.conn.execute(
                "UPDATE hosted_bots SET status = ?, pid = 0, stopped_at = ? WHERE bot_id = ?",
                (status, now, bot_id)
            )
        await self.conn.commit()

    async def delete_bot(self, bot_id: int):
        await self.conn.execute("DELETE FROM hosted_bots WHERE bot_id = ?", (bot_id,))
        await self.conn.execute("DELETE FROM bot_logs WHERE bot_id = ?", (bot_id,))
        await self.conn.commit()

    async def get_all_running_bots(self) -> List[Dict]:
        cursor = await self.conn.execute(
            "SELECT * FROM hosted_bots WHERE status = 'running'"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_total_bots(self) -> int:
        cursor = await self.conn.execute("SELECT COUNT(*) FROM hosted_bots")
        row = await cursor.fetchone()
        return row[0]

    # ─────────────── Log Operations ───────────────
    async def add_log(self, bot_id: int, message: str, log_type: str = "stdout"):
        now = time.time()
        await self.conn.execute(
            "INSERT INTO bot_logs (bot_id, log_type, message, created_at) VALUES (?, ?, ?, ?)",
            (bot_id, log_type, message, now)
        )
        await self.conn.commit()

    async def get_logs(self, bot_id: int, limit: int = 50) -> List[Dict]:
        cursor = await self.conn.execute(
            "SELECT * FROM bot_logs WHERE bot_id = ? ORDER BY created_at DESC LIMIT ?",
            (bot_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def clear_logs(self, bot_id: int):
        await self.conn.execute("DELETE FROM bot_logs WHERE bot_id = ?", (bot_id,))
        await self.conn.commit()

    # ─────────────── Admin Group ───────────────
    async def set_admin_group(self, group_id: int):
        await self.conn.execute("DELETE FROM admin_group")
        await self.conn.execute(
            "INSERT INTO admin_group (group_id) VALUES (?)", (group_id,)
        )
        await self.conn.commit()

    async def get_admin_group(self) -> Optional[int]:
        cursor = await self.conn.execute("SELECT group_id FROM admin_group LIMIT 1")
        row = await cursor.fetchone()
        return row[0] if row else None

    # ─────────────── Activity Log ───────────────
    async def log_activity(self, user_id: int, action: str, details: str = ""):
        now = time.time()
        await self.conn.execute(
            "INSERT INTO activity_log (user_id, action, details, created_at) VALUES (?, ?, ?, ?)",
            (user_id, action, details, now)
        )
        await self.conn.commit()


# Global database instance
db = Database()
