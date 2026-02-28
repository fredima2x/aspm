#! /bin/python
import hashlib
import os
import socket
import time
import json as js
import logging
import ssl

# Client configuration
SERVER_HOST = "fredima.de"  # IP-Adresse des Servers
CERT_PATH = os.path.expanduser('~/.aspm_cert.pem')
SERVER_PORT = 8280
CERT_PORT = 8281
GUI_ENABLED = False  # Set to True if you have a GUI implementation

def INIT():
    global log
    logging.basicConfig(level="DEBUG", format='%(asctime)s - %(levelname)s - %(message)s')
    log = logging.getLogger(__name__)

class ServerConnection:
    def __init__(self, host, port):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.socket = None
        self.connect()
    
    def connect(self):
        try:
            try:
                fetch_certificate(self.host, CERT_PORT)  # Zertifikat einmalig vom Server holen
            except Exception as e:
                log.error(f"Failed to fetch certificate: {e}")
                exit(1)
            self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.context.load_verify_locations(CERT_PATH)
            self.raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = self.context.wrap_socket(self.raw_sock, server_hostname=self.host)
            self.socket.connect((self.host, self.port))
            self.logger.info(f"Connected to server at {self.host}:{self.port}")
        except ConnectionRefusedError:
            self.logger.error(f"Failed to connect to server at {self.host}:{self.port}")
            raise
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise
    
    def verify_credentials(self, username, password, sign_up=False):
        if not username or not password:
            self.logger.error("Username and password cannot be empty")
            return None
        
        sign_up_command = "send_newuser" if sign_up else "send_creds"
        creds = f"{sign_up_command};{username};{password}"
        try:
            self.socket.sendall(creds.encode())
            response = self.socket.recv(1024).decode()
            return response
        except Exception as e:
            self.logger.error(f"Error during credential verification: {e}")
            return None
    
    def group_list(self):
        self.logger.info("Listing chats...")
        try:
            self.socket.sendall("get_chats".encode())
            response = self.socket.recv(4096).decode()
            if response.startswith("send_chats;"):
                chats_json = response[11:]  # Remove "send_chats;" prefix
                chats = js.loads(chats_json)
                self.logger.info(f"Retrieved {len(chats)} chats")
                return chats
            elif response == "None":
                self.logger.info("No chats found.")
                return []
            else:
                self.logger.warning(f"Invalid Server Response: {response}")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving chat list: {e}")
            return None
    
    def group_create(self, name, properties="{}"):
        if not name:
            self.logger.error("Chat name cannot be empty")
            return False
        
        self.logger.info(f"Creating new chat: {name}")
        try:
            self.socket.sendall(f"new_chat;{name}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response.startswith("chat_created"):
                self.logger.info("Chat created successfully!")
                return True
            else:
                self.logger.error(f"Failed to create chat: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error creating chat: {e}")
            return False
    
    def message_new(self, chat, message_content, properties="{}"):
        if not chat or not message_content:
            self.logger.error("Chat ID and message content cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"send_message;{chat};{message_content}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "message_saved":
                self.logger.info("Message sent successfully")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return None
    
    def message_getall(self, chat, limit=100, offset=0):
        if not chat:
            self.logger.error("Chat ID cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"get_messages;{chat};{limit};{offset}".encode())
            time.sleep(0.1)
            response = self.socket.recv(4096).decode()
            if response.startswith("messages;"):
                json_response = response[9:]  # Remove "messages;" prefix
                messages = js.loads(json_response)
                self.logger.info(f"Retrieved {len(messages) if messages else 0} messages")
                return messages
            else:
                self.logger.warning(f"Invalid server response: {response}")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving messages: {e}")
            return None
    
    def group_useradd(self, chat, user):
        if not chat or not user:
            self.logger.error("Chat ID and user identifier cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"add_user_to_chat;{chat};{user}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "user_added":
                self.logger.info(f"User {user} added to chat {chat}")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error adding user to chat: {e}")
            return None
    
    def group_userrm(self, chat, user):
        if not chat or not user:
            self.logger.error("Chat ID and user identifier cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"remove_user_from_chat;{chat};{user}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "user_removed":
                self.logger.info(f"User {user} removed from chat {chat}")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error removing user from chat: {e}")
            return None
    
    def delete_account(self):
        self.logger.info("Requesting account deletion...")
        try:
            self.socket.sendall("delete_account".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "account_deleted":
                self.logger.info("Account deleted successfully")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error deleting account: {e}")
            return None
    def delete_chat(self, chat_id=None):
        if not chat_id:
            self.logger.error("Chat ID cannot be empty")
            return None
        
        self.logger.info(f"Requesting deletion of chat {chat_id}...")
        try:
            self.socket.sendall(f"delete_chat;{chat_id}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "chat_deleted":
                self.logger.info(f"Chat {chat_id} deleted successfully")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error deleting chat: {e}")
            return None
    def delete_message(self, message_id=None):
        if not message_id:
            self.logger.error("Message ID cannot be empty")
            return None
        
        self.logger.info(f"Requesting deletion of message {message_id}...")

        try:
            self.socket.sendall(f"delete_message;{message_id}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "message_deleted":
                self.logger.info(f"Message {message_id} deleted successfully")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error deleting message: {e}")
            return None


def fetch_certificate(host, port=8281):
    """Holt das Zertifikat einmalig vom SSL-Handshake und speichert es lokal."""
    if os.path.exists(CERT_PATH):
        return

    print(f"Erstes Verbinden – lade Zertifikat von {host}:{port}...")

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # Nur beim Holen!

    with socket.create_connection((host, port)) as raw_sock:
        with context.wrap_socket(raw_sock, server_hostname=host) as ssock:
            cert_der = ssock.getpeercert(binary_form=True)
            cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)

            fingerprint = hashlib.sha256(cert_der).hexdigest()
            fp_fmt = ":".join(fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2))

            with open(CERT_PATH, "w") as f:
                f.write(cert_pem)

            print(f"Zertifikat gespeichert unter {CERT_PATH}")
            print(f"WICHTIG: Bitte prüfe den Fingerprint beim Server:")
            print(f"sha256 Fingerprint={fp_fmt}")

def main():
    INIT()
    conn = ServerConnection(SERVER_HOST, SERVER_PORT)
    if GUI_ENABLED:
        log.info("GUI mode is enabled, but GUI implementation is not provided in this code snippet.")
        ### HIER! GUI-Implementierung einfügen
    else:
        log.info("Running in CLI mode. You can implement CLI interactions here.")
        while True:
            command = input("Enter command >>> ").strip().lower()
            if command == "list":
                chats = conn.group_list()
                print(chats)
            elif command == "signup":
                username = input("Enter username: ")
                password = input("Enter password: ")
                response = conn.verify_credentials(username, password, sign_up=True)
                print(response)
            elif command == "login":
                username = input("Enter username: ")
                password = input("Enter password: ")
                response = conn.verify_credentials(username, password, sign_up=False)
                print(response)
            elif command == "create":
                name = input("Enter chat name: ")
                conn.group_create(name)
            elif command == "send":
                chat_id = input("Enter chat ID: ")
                message = input("Enter message content: ")
                conn.message_new(chat_id, message)
            elif command == "get":
                chat_id = input("Enter chat ID: ")
                messages = conn.message_getall(chat_id)
                print(messages)
            elif command == "adduser":
                chat_id = input("Enter chat ID: ")
                user = input("Enter user identifier to add: ")
                conn.group_useradd(chat_id, user)
            elif command == "rmuser":
                chat_id = input("Enter chat ID: ")
                user = input("Enter user identifier to remove: ")
                conn.group_userrm(chat_id, user)
            elif command == "delete_account":
                confirmation = input("Are you sure you want to delete your account? This action cannot be undone. (yes/no): ")
                if confirmation.lower() == "yes":
                    conn.delete_account()
                else:
                    log.info("Account deletion cancelled.")
            elif command == "delete_chat":
                chat_id = input("Enter chat ID to delete: ")
                confirmation = input(f"Are you sure you want to delete chat {chat_id}? This action cannot be undone. (yes/no): ")
                if confirmation.lower() == "yes":
                    conn.delete_chat(chat_id)
                else:
                    log.info("Chat deletion cancelled.")
            elif command == "delete_message":
                chat_id = input("Enter chat ID: ")
                message_id = input("Enter message ID to delete: ")
                confirmation = input(f"Are you sure you want to delete message {message_id} in chat {chat_id}? This action cannot be undone. (yes/no): ")
                if confirmation.lower() == "yes":
                    conn.delete_message(chat_id, message_id)
                else:
                    log.info("Message deletion cancelled.")
            elif command == "help":
                log.info("Available commands: list, create, send, get, adduser, rmuser, quit, signup, login, delete_account, delete_chat")
            elif command == "quit":
                log.info("Exiting client.")
                break
            else:
                log.warning("Unknown command. Please try again.")

if __name__ == "__main__":
    main()
