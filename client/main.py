#! /bin/python
import socket
import threading
import time
import json as js
import logging

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
        self.logger = logging.Logger(__name__, 0)
        self.connect()
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print(f"Connected to server at {self.host}:{self.port}")
    # Additional methods for sending/receiving data can be added here
    def verify_credentials(self, username, password, sign_up=False):
        sign_up_command = "send_newuser" if sign_up else "send_creds"
        creds = f"{sign_up_command};{username};{password}"
        self.socket.sendall(creds.encode())
        response = self.socket.recv(1024).decode()
        return response
    def group_list(self):
        self.logger.info("Listing chats...")
        self.socket.sendall("get_chats".encode())
        response = self.socket.recv(4096).decode()
        if response.startswith("send_chats;"):
            chats_json = response[11:]  # Remove "send_chats;" prefix
            chats = js.loads(chats_json)
            return chats
        elif response == "None":
            self.logger.info("No Chats found.")
        else:
            self.logger.warning("Invalid Server Response!")
    def group_create(self, name, properties="{}"): # Properties will be implemented later
        print("Creating new chat...")
        self.socket.sendall(f"new_chat;{name}".encode())
        time.sleep(0.5)
        response = self.socket.recv(1024).decode()
        if response.startswith("chat_created"):
            self.logger.info("Chat created successfully!")
        else:
            self.logger.info("Failed to create chat.")
    def message_new(self, chat, message_content, properties="{}"): # Properties will be implemented later
        self.socket.sendall(f"send_message;{chat};{message_content}".encode())
        time.sleep(0.5)
        response = self.socket.recv(1024).decode()
        return response
    def message_getall(self, chat):
        self.socket.sendall(f"get_messages;{chat}".encode())
        time.sleep(0.5)
        json_response = str(self.socket.recv(4096).decode())
        response = js.loads(json_response)
        return response
    def group_useradd(self, chat, user):
        identifier = user
        self.socket.sendall(f"add_user_to_chat;{chat};{identifier}".encode())
        time.sleep(0.5)
        response = self.socket.recv(1024).decode()
        return response
    def group_userrm(self, chat, user):
        identifier = user
        self.socket.sendall(f"remove_user_from_chat;{chat};{identifier}".encode())
        time.sleep(0.5)
        response = self.socket.recv(1024).decode()
        return response
    
def main():
    conn = ServerConnection("127.0.0.1", 8080)


if __name__ == "__main__":
    main()    