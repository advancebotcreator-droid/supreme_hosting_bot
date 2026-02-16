import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_premium INTEGER DEFAULT 0,
                    premium_until TEXT,
                    is_admin INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    joined_date TEXT,
                    last_active TEXT,
                    total_bots INTEGER DEFAULT 0,
                    total_uploads INTEGER DEFAULT 0
                )
            ''')
            
            # Hosted bots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hosted_bots (
                    bot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    bot_name TEXT,
                    file_name TEXT,
                    file_path TEXT,
                    file_type TEXT,
                    file_size INTEGER,
                    process_id INTEGER,
                    status TEXT DEFAULT 'stopped',
                    created_date TEXT,
                    last_started TEXT,
                    errors TEXT,
                    installed_modules TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Admin actions log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action_type TEXT,
                    target_user_id INTEGER,
                    details TEXT,
                    timestamp TEXT
                )
            ''')
            
            # Statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_date TEXT,
                    total_users INTEGER,
                    active_bots INTEGER,
                    total_uploads INTEGER,
                    premium_users INTEGER
                )
            ''')
    
    # User Management
    def add_user(self, user_id, username, first_name, last_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, joined_date, last_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
            
            # Update last active
            cursor.execute('''
                UPDATE users SET last_active = ? WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
    
    def get_user(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
    
    def is_premium(self, user_id):
        user = self.get_user(user_id)
        if not user or not user['is_premium']:
            return False
        
        # Check if premium expired
        if user['premium_until']:
            premium_until = datetime.fromisoformat(user['premium_until'])
            if datetime.now() > premium_until:
                self.remove_premium(user_id)
                return False
        
        return True
    
    def is_admin(self, user_id):
        user = self.get_user(user_id)
        return user and user['is_admin'] == 1
    
    def is_banned(self, user_id):
        user = self.get_user(user_id)
        return user and user['is_banned'] == 1
    
    def add_premium(self, user_id, days):
        premium_until = (datetime.now() + timedelta(days=days)).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET is_premium = 1, premium_until = ?
                WHERE user_id = ?
            ''', (premium_until, user_id))
    
    def remove_premium(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET is_premium = 0, premium_until = NULL
                WHERE user_id = ?
            ''', (user_id,))
    
    def add_admin(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET is_admin = 1 WHERE user_id = ?
            ''', (user_id,))
    
    def remove_admin(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET is_admin = 0 WHERE user_id = ?
            ''', (user_id,))
    
    def ban_user(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET is_banned = 1 WHERE user_id = ?
            ''', (user_id,))
    
    def unban_user(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET is_banned = 0 WHERE user_id = ?
            ''', (user_id,))
    
    def get_all_admins(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE is_admin = 1')
            return cursor.fetchall()
    
    def get_all_premium_users(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE is_premium = 1')
            return cursor.fetchall()
    
    def get_all_users(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            return cursor.fetchall()
    
    # Bot Management
    def add_hosted_bot(self, user_id, bot_name, file_name, file_path, file_type, file_size):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO hosted_bots 
                (user_id, bot_name, file_name, file_path, file_type, file_size, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, bot_name, file_name, file_path, file_type, file_size, 
                  datetime.now().isoformat()))
            
            # Update user stats
            cursor.execute('''
                UPDATE users 
                SET total_bots = total_bots + 1, total_uploads = total_uploads + 1
                WHERE user_id = ?
            ''', (user_id,))
            
            return cursor.lastrowid
    
    def get_user_bots(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM hosted_bots WHERE user_id = ?
            ''', (user_id,))
            return cursor.fetchall()
    
    def get_bot(self, bot_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM hosted_bots WHERE bot_id = ?', (bot_id,))
            return cursor.fetchone()
    
    def update_bot_status(self, bot_id, status, process_id=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if process_id:
                cursor.execute('''
                    UPDATE hosted_bots 
                    SET status = ?, process_id = ?, last_started = ?
                    WHERE bot_id = ?
                ''', (status, process_id, datetime.now().isoformat(), bot_id))
            else:
                cursor.execute('''
                    UPDATE hosted_bots SET status = ? WHERE bot_id = ?
                ''', (status, bot_id))
    
    def update_bot_errors(self, bot_id, errors):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE hosted_bots SET errors = ? WHERE bot_id = ?
            ''', (errors, bot_id))
    
    def add_installed_module(self, bot_id, module_name):
        bot = self.get_bot(bot_id)
        modules = json.loads(bot['installed_modules']) if bot['installed_modules'] else []
        if module_name not in modules:
            modules.append(module_name)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE hosted_bots SET installed_modules = ? WHERE bot_id = ?
            ''', (json.dumps(modules), bot_id))
    
    def delete_bot(self, bot_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM hosted_bots WHERE bot_id = ?', (bot_id,))
    
    # Admin Logs
    def add_admin_log(self, admin_id, action_type, target_user_id, details):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_logs 
                (admin_id, action_type, target_user_id, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (admin_id, action_type, target_user_id, details, 
                  datetime.now().isoformat()))
    
    # Statistics
    def get_statistics(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total FROM users')
            total_users = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_premium = 1')
            premium_users = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM hosted_bots WHERE status = 'running'")
            active_bots = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as total FROM hosted_bots')
            total_bots = cursor.fetchone()['total']
            
            cursor.execute('SELECT SUM(total_uploads) as total FROM users')
            total_uploads = cursor.fetchone()['total'] or 0
            
            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'active_bots': active_bots,
                'total_bots': total_bots,
                'total_uploads': total_uploads
            }

# Initialize database
db = Database()
