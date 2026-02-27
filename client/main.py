#! /bin/python
import socket
import threading
import time
import json as js
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Client configuration
SERVER_HOST = "localhost"  # Server-Adresse (z.B. "localhost" oder "192.168.1.100")
SERVER_PORT = 8080         # Server-Port (muss mit dem Server übereinstimmen)

# DEBUG: DONT CHANGE THIS
GUI_ENABLED = False

class ServerConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.connect()
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.info(f"Connected to server at {self.host}:{self.port}")
        except ConnectionRefusedError:
            logger.error(f"Failed to connect to server at {self.host}:{self.port}")
            raise
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
    
    def verify_credentials(self, username, password, sign_up=False):
        if not username or not password:
            logger.error("Username and password cannot be empty")
            return None
        
        sign_up_command = "send_newuser" if sign_up else "send_creds"
        creds = f"{sign_up_command};{username};{password}"
        try:
            self.socket.sendall(creds.encode())
            response = self.socket.recv(1024).decode()
            return response
        except Exception as e:
            logger.error(f"Error during credential verification: {e}")
            return None
    
    def group_list(self):
        logger.info("Listing chats...")
        try:
            self.socket.sendall("get_chats".encode())
            response = self.socket.recv(4096).decode()
            if response.startswith("send_chats;"):
                chats_json = response[11:]  # Remove "send_chats;" prefix
                chats = js.loads(chats_json)
                logger.info(f"Retrieved {len(chats)} chats")
                return chats
            elif response == "None":
                logger.info("No chats found.")
                return []
            else:
                logger.warning(f"Invalid Server Response: {response}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving chat list: {e}")
            return None
    
    def group_create(self, name, properties="{}"):
        if not name:
            logger.error("Chat name cannot be empty")
            return False
        
        logger.info(f"Creating new chat: {name}")
        try:
            self.socket.sendall(f"new_chat;{name}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response.startswith("chat_created"):
                logger.info("Chat created successfully!")
                return True
            else:
                logger.error(f"Failed to create chat: {response}")
                return False
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            return False
    
    def message_new(self, chat, message_content, properties="{}"):
        if not chat or not message_content:
            logger.error("Chat ID and message content cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"send_message;{chat};{message_content}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "message_saved":
                logger.info("Message sent successfully")
            else:
                logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    def message_getall(self, chat, limit=100, offset=0):
        if not chat:
            logger.error("Chat ID cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"get_messages;{chat};{limit};{offset}".encode())
            time.sleep(0.1)
            response = self.socket.recv(4096).decode()
            if response.startswith("messages;"):
                json_response = response[9:]  # Remove "messages;" prefix
                messages = js.loads(json_response)
                logger.info(f"Retrieved {len(messages) if messages else 0} messages")
                return messages
            else:
                logger.warning(f"Invalid server response: {response}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}")
            return None
    
    def group_useradd(self, chat, user):
        if not chat or not user:
            logger.error("Chat ID and user identifier cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"add_user_to_chat;{chat};{user}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "user_added":
                logger.info(f"User {user} added to chat {chat}")
            else:
                logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error adding user to chat: {e}")
            return None
    
    def group_userrm(self, chat, user):
        if not chat or not user:
            logger.error("Chat ID and user identifier cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"remove_user_from_chat;{chat};{user}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "user_removed":
                logger.info(f"User {user} removed from chat {chat}")
            else:
                logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error removing user from chat: {e}")
            return None

    
def main():
    conn = ServerConnection(SERVER_HOST, SERVER_PORT)


if __name__ == "__main__":
    main()
