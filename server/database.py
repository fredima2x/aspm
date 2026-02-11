import sqlite3
import hashlib
import secrets

class DatabaseManager:
    def __init__(self, db_path="messenger.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    def create_user(self, nickname, password):
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        self.cursor.execute(
        "INSERT INTO users (nickname, password_hash, salt) VALUES (?, ?, ?)",
        (nickname, password_hash, salt)
        )
        self.connection.commit()
        
