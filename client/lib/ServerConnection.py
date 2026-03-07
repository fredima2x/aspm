import socket
import ssl
import json as js
import time
import logging
import os

import lib.normals as normals

def fetch_certificate(host, port=normals.cert_port):
    if os.path.exists(normals.CERT_PATH):
        return
    print(f"Erstes Verbinden – lade Zertifikat von {host}:{port} ...")
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            cert_pem = sock.recv(8192).decode()
            with open(normals.CERT_PATH, "w") as f:
                f.write(cert_pem)
        print(f"Zertifikat gespeichert: {normals.CERT_PATH}")
    except Exception as e:
        logging.error(f"Fehler beim Abrufen des Zertifikats: {e}")
        raise

class ServerConnection:
    def __init__(self, host, port, cert_port):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.cert_port = cert_port
        self.CERT_PATH = normals.CERT_PATH
        self.socket = None
        try:
            self.connect()
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {e}")
    
    def connect(self):
        try:
            fetch_certificate(self.host, self.cert_port)
        except Exception as e:
            self.logger.error(f"Failed to fetch certificate: {e}")
            exit(1)
        try:
            self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.context.load_verify_locations(self.CERT_PATH)
            self.raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = self.context.wrap_socket(self.raw_sock, server_hostname=self.host)
            self.socket.connect((self.host, self.port))
            self.logger.info(f"Connected to server at {self.host}:{self.port}")
        except ConnectionRefusedError:
            self.logger.error(f"Failed to connect to server at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Connection error: {e}")

    def close(self):
        if self.socket:
            self.socket.close()
            self.logger.info("Connection closed")

    def status(self):
        try:
            # Nicht-blockierend prüfen ob Socket noch offen
            self.socket.getpeername()
            return True
        except Exception:
            return False


    def verify_credentials(self, username, password, sign_up=False):
        if not username or not password:
            self.logger.error("Username and password cannot be empty")
            return None
        cmd = "send_newuser" if sign_up else "send_creds"
        try:
            self.socket.sendall(f"{cmd};{username};{password}".encode())
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error during credential verification: {e}")
            return None

    def group_list(self):
        # Returns: [{"chat_id":1,"creator_id":1,"members":[1,2],...}, ...]
        self.logger.info("Listing chats...")
        try:
            self.socket.sendall("get_chats".encode())
            response = self.socket.recv(4096).decode()
            if response.startswith("send_chats;"):
                chats = js.loads(response[11:])
                self.logger.info(f"Retrieved {len(chats)} chats")
                return chats
            elif response == "None":
                return []
            self.logger.warning(f"Invalid Server Response: {response}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving chat list: {e}")
            return None

    def group_create(self, name, properties="{}"):
        if not name:
            return False
        self.logger.info(f"Creating new chat: {name}")
        try:
            self.socket.sendall(f"new_chat;{name}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response.startswith("chat_created"):
                self.logger.info("Chat created successfully!")
                return True
            self.logger.error(f"Failed to create chat: {response}")
            return False
        except Exception as e:
            self.logger.error(f"Error creating chat: {e}")
            return False

    def message_new(self, chat, message_content, properties="{}"):
        if not chat or not message_content:
            return None
        try:
            self.socket.sendall(f"send_message;{chat};{message_content}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return None

    def message_getall(self, chat, limit=100, offset=0):
        # Returns: [{"message_id":1,"sender_id":2,"content":"...","send_at":"..."}, ...]
        # Newest message first!
        if not chat:
            return None
        try:
            self.socket.sendall(f"get_messages;{chat};{limit};{offset}".encode())
            time.sleep(0.1)
            response = self.socket.recv(4096).decode()
            if response.startswith("messages;"):
                messages = js.loads(response[9:])
                self.logger.info(f"Retrieved {len(messages) if messages else 0} messages")
                return messages
            self.logger.warning(f"Invalid server response: {response}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving messages: {e}")
            return None

    def group_useradd(self, chat, user):
        if not chat or not user:
            return None
        try:
            self.socket.sendall(f"add_user_to_chat;{chat};{user}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error adding user: {e}")
            return None

    def group_userrm(self, chat, user):
        if not chat or not user:
            return None
        try:
            self.socket.sendall(f"remove_user_from_chat;{chat};{user}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error removing user: {e}")
            return None

    def delete_account(self):
        try:
            self.socket.sendall("delete_account".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error deleting account: {e}")
            return None

    def delete_chat(self, chat_id=None):
        if not chat_id:
            return None
        try:
            self.socket.sendall(f"delete_chat;{chat_id}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error deleting chat: {e}")
            return None

    def delete_message(self, message_id=None):
        if not message_id:
            return None
        try:
            self.socket.sendall(f"delete_message;{message_id}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error deleting message: {e}")
            return None
    
    def get_myuser_id(self):
        try:
            self.socket.sendall(f"get_user_id".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response.startswith("user_id;"):
                user_id = int(response[8:])
                self.logger.info(f"User ID for is {user_id}")
                return user_id
            self.logger.warning(f"Invalid server response: {response}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving user ID: {e}")
            return None
    
    def get_user_info(self, user_identifier):
        try:
            self.socket.sendall(f"get_user_info;{user_identifier}".encode())
            time.sleep(0.1)
            response = self.socket.recv(4096).decode()
            if response.startswith("user_info;"):
                user_info = js.loads(response[10:])
                self.logger.info(f"Retrieved user info for {user_identifier}: {user_info}")
                return user_info
            self.logger.warning(f"Invalid server response: {response}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving user info: {e}")
            return None