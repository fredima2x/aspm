import sqlite3
import hashlib
import secrets
import logging

class DatabaseManager:
    def __init__(self, db_path="messenger.db"):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO) 
        self.db_path = db_path
        self._init_database()
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    def _init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL, 
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                chat_id INTEGER,
                content TEXT NOT NULL,
                properties TEXT, 
                send_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                members TEXT,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    def create_user(self, nickname, password):
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (nickname, password_hash, salt) VALUES (?, ?, ?)",
                (nickname, password_hash, salt)
            )
            conn.commit()
            user_id = cursor.lastrowid
            return user_id
        except sqlite3.IntegrityError as e:
            self.logger.info(f"sqlite.IntegrityError: could not save user! {e}")
            return None  
        finally:
            conn.close()
    def verify_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT user_id, password_hash, salt FROM users WHERE nickname = ?",
                (username,)
            )
            result = cursor.fetchone()
            if result is None:
                return None
            user_id, stored_hash, salt = result
            input_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            if input_hash == stored_hash:
                return user_id 
            else:
                return None 
        finally:
            conn.close()
    def save_message(self, sender_id, chat_id, content, properties=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try: 
            cursor.execute(
                "INSERT INTO messages (sender_id, chat_id, content, properties) VALUES (?, ?, ?, ?)",
                (sender_id, chat_id, content, properties)
            )
            conn.commit()
        except Exception as e:  
            self.logger.critical(f"Failed to save message! Error: {e}")
        finally:
            conn.close()
    def load_messages(self, chat_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT sender_id, content, properties FROM messages WHERE chat_id = ?",
                (chat_id,) 
            )
            result = cursor.fetchall()
            return result  
        except Exception as e:  
            self.logger.error(f"Could not load messages! Error: {e}")
            return []
        finally:
            conn.close()
    def new_chat(self, creator_id, properties=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO chats (creator_id, properties) VALUES (?, ?)",
                (creator_id, properties)
            )
            conn.commit()
        except:
            return None
        finally:
            conn.close()

    def delete_chat(self, chat_id, run_user):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM chats WHERE chat_id = ? AND creator_id = ?",
                (chat_id, run_user)
            )
        except


    def add_to_chat(self, chat_id, user_id):
        pass


