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

        try:
            cursor.execute("""
                SELECT user_id, password_hash, salt 
                FROM users 
                WHERE nickname = ?
            """, (username,))
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


