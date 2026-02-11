import sqlite3
import hashlib
import secrets

class DatabaseManager:
    def __init__(self, db_path="messenger.db"):
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
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()  
    def verify_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        all_users = cursor.fetchall()
        for user in all_users:
            if user[1] == username:
                 
        
    