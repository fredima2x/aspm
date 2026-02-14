import sqlite3
import hashlib
import secrets
import logging
import json

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
    def delete_chat(self, chat_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM chats WHERE chat_id = ?",
                (chat_id,)
            )
            conn.commit()  
            return True
        except Exception as e:  
            self.logger.error(f"DELETE_CHAT: Fehler - {str(e)}")
            return False
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
            chat_id = cursor.lastrowid 
            return chat_id
        except Exception as e:
            self.logger.error(f"NEW_CHAT: Fehler - {str(e)}")
            return None
        finally:
            conn.close()
    def add_to_chat(self, chat_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT members, creator_id FROM chats WHERE chat_id = ?",
                (chat_id,)
            )
            result = cursor.fetchone() 
            if result is None:
                self.logger.error(f"ADD_TO_CHAT: Chat {chat_id} existiert nicht")
                conn.close()
                return False
            members_json, creator_id = result
            if members_json:
                members = json.loads(members_json)
            else:
                members = [creator_id]
            if user_id in members:
                self.logger.warning(f"ADD_TO_CHAT: User {user_id} ist bereits in Chat {chat_id}")
                conn.close()
                return False
            members.append(user_id)
            members_json = json.dumps(members)
            cursor.execute(
                "UPDATE chats SET members = ? WHERE chat_id = ?",
                (members_json, chat_id)
            )
            conn.commit()
            self.logger.info(f"ADD_TO_CHAT: User {user_id} erfolgreich zu Chat {chat_id} hinzugefügt")
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"ADD_TO_CHAT: Fehler - {str(e)}")
            conn.rollback()
            conn.close()
            return False
    def get_user_chats(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT chat_id, creator_id, members, properties, created_at FROM chats"
            )
            all_chats = cursor.fetchall()
            user_chats = []
            for chat in all_chats:
                chat_id, creator_id, members_json, properties, created_at = chat
                if members_json:
                    members = json.loads(members_json)
                    if user_id in members or creator_id == user_id:
                        user_chats.append({
                            'chat_id': chat_id,
                            'creator_id': creator_id,
                            'members': members,
                            'properties': properties,
                            'created_at': created_at
                        })
            return user_chats
        except Exception as e:
            self.logger.error(f"GET_USER_CHATS: Fehler - {str(e)}")
            return []
        finally:
            conn.close()
    def get_chat_members(self, chat_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT members, creator_id FROM chats WHERE chat_id = ?",
                (chat_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return None
            members_json, creator_id = result
            if members_json:
                members = json.loads(members_json)
            else:
                members = [creator_id]
            return members
        except Exception as e:
            self.logger.error(f"GET_CHAT_MEMBERS: Fehler - {str(e)}")
            return None
        finally:
            conn.close()
    def remove_from_chat(self, chat_id, user_id):
        """User aus Chat entfernen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT members, creator_id FROM chats WHERE chat_id = ?",
                (chat_id,)
            )
            result = cursor.fetchone()
            if result is None:
                return False
            members_json, creator_id = result
            if members_json:
                members = json.loads(members_json)
            else:
                members = [creator_id]
            if user_id not in members:
                return False
            members.remove(user_id)
            members_json = json.dumps(members)
            cursor.execute(
                "UPDATE chats SET members = ? WHERE chat_id = ?",
                (members_json, chat_id)
            )
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"REMOVE_FROM_CHAT: Fehler - {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    def get_user_by_id(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT user_id, nickname, properties, created_at FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    'user_id': result[0],
                    'nickname': result[1],
                    'properties': result[2],
                    'created_at': result[3]
                }
            return None
        finally:
            conn.close()
    def get_user_by_nickname(self, nickname):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT user_id, nickname, properties FROM users WHERE nickname = ?",
                (nickname,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    'user_id': result[0],
                    'nickname': result[1],
                    'properties': result[2]
                }
            return None
        finally:
            conn.close()
    def search_users(self, query):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT user_id, nickname FROM users WHERE nickname LIKE ?",
                (f"%{query}%",)
            )
            results = cursor.fetchall()
            return [{'user_id': r[0], 'nickname': r[1]} for r in results]
        finally:
            conn.close()
    def get_messages(self, chat_id, limit=50, offset=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT message_id, sender_id, content, properties, send_at 
                FROM messages 
                WHERE chat_id = ? 
                ORDER BY send_at DESC 
                LIMIT ? OFFSET ?""",
                (chat_id, limit, offset)
            )
            results = cursor.fetchall()
            return [{
                'message_id': r[0],
                'sender_id': r[1],
                'content': r[2],
                'properties': r[3],
                'send_at': r[4]
            } for r in results]
        finally:
            conn.close()
    def delete_message(self, message_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT sender_id FROM messages WHERE message_id = ?",
                (message_id,)
            )
            result = cursor.fetchone()
            if result is None or result[0] != user_id:
                return False
            
            cursor.execute(
                "DELETE FROM messages WHERE message_id = ?",
                (message_id,)
            )
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"DELETE_MESSAGE: Fehler - {str(e)}")
            return False
        finally:
            conn.close()
