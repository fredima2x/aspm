#!/bin/python
import socket
import threading
import logging
import datasm
import json as js

VERSION = "1.6.0"

SERVER_PORT = 8080          # Standard Port: 8080

# Lists:
clients = []  
clients_lock = threading.Lock()  
clients_data = {}  # Dictionary to store client-specific data, e.g., user_id
clients_data_lock = threading.Lock()  # Lock for synchronizing access to clients_data

class ClientHandler(threading.Thread):
    def __init__(self, client_socket, addr):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.addr = addr
        self.db = datasm.DatabaseManager()
        self.verified_user = False
        self.user_id = None
    def run(self):
        global clients, clients_lock, clients_data, clients_data_lock
        logger.info(f"Verbindung von {self.addr} akzeptiert")
        clients_lock.acquire()
        clients.append(self.client_socket)
        clients_lock.release()
        while True:
            try:
                data = self.client_socket.recv(1024)
            except OSError as e:
                logger.error(f"Socket-Fehler bei Client {self.addr}: {e}")
                break
            except Exception as e:
                logger.error(f"Unerwarteter Fehler bei Client {self.addr}: {e}")
                break
            if not data:
                break
            message = data.decode()
            ready_message = message.split(";")
            # Commands for unverified users
            if ready_message[0] == "send_creds":
                logger.info("Got send_creds Request!")
                if len(ready_message) < 3:
                    logger.error("Incomplete send_creds request")
                    continue
                username = ready_message[1]
                password = ready_message[2]
                self.verify_user(username, password)
            elif ready_message[0] == "send_newuser":
                logger.info("Got send_newuser Request!")
                if len(ready_message) < 3:
                    logger.error("Incomplete send_newuser request")
                    continue
                username = ready_message[1]
                password = ready_message[2]
                self.new_user(username, password)
            # Commands for verified users
            elif self.verified_user:
                try:
                    if ready_message[0] == "get_chats":
                        self.get_chats()
                    elif ready_message[0] == "add_user_to_chat":
                        if len(ready_message) < 3:
                            logger.error("Incomplete add_user_to_chat request")
                            continue
                        chat_id = int(ready_message[1])
                        identifier = ready_message[2]
                        self.add_user_to_chat(chat_id, identifier)
                    elif ready_message[0] == "remove_user_from_chat":
                        if len(ready_message) < 3:
                            logger.error("Incomplete remove_user_from_chat request")
                            continue
                        chat_id = int(ready_message[1])
                        identifier = ready_message[2]
                        self.remove_user_from_chat(chat_id, identifier)
                    elif ready_message[0] == "get_messages":
                        if len(ready_message) < 4:
                            logger.error("Incomplete get_messages request")
                            continue
                        chat_id = int(ready_message[1])
                        limit = int(ready_message[2])
                        offset = int(ready_message[3])
                        self.get_messages(chat_id, limit, offset)
                    elif ready_message[0] == "send_message":
                        if len(ready_message) < 3:
                            logger.error("Incomplete send_message request")
                            continue
                        chat_id = int(ready_message[1])
                        message_content = ready_message[2]
                        self.send_message(chat_id, message_content)
                    elif ready_message[0] == "new_chat":
                        if len(ready_message) < 2:
                            logger.error("Incomplete new_chat request")
                            continue
                        chat_name = ready_message[1]
                        self.new_chat(chat_name)
                except ValueError as e:
                    logger.error(f"Invalid parameter format: {e}")
                    self.client_socket.sendall("invalid_parameters".encode())
        # Cleanup on disconnect
        clients_lock.acquire()
        clients.remove(self.client_socket)
        clients_lock.release()
        clients_data_lock.acquire()
        if self.client_socket in clients_data:
            del clients_data[self.client_socket]
        clients_data_lock.release()
        logger.info(f"Verbindung von {self.addr} geschlossen!")
        self.client_socket.close()
    def new_user(self, username, password):
        if username is not None and password is not None:
            user_id = self.db.create_user(username, password)
            if user_id:
                self.verified_user = True
                self.user_id = user_id
                clients_data_lock.acquire()
                clients_data[self.client_socket] = {"user_id": user_id}
                clients_data_lock.release()
                self.client_socket.sendall("verified".encode())
                logger.info(f"New user {username} created and verified")
            else:
                self.client_socket.sendall("invalid_creds".encode())
        else:
            self.client_socket.sendall("invalid_creds".encode())
    def verify_user(self, username, password):
        if username is not None and password is not None:
            verify_status = self.db.verify_user(username, password)
            if verify_status is None:
                self.client_socket.sendall("invalid".encode())
                logger.debug(f"Wrong Creds! {self.addr}")
            else:
                self.user_id = verify_status
                self.verified_user = True
                logger.info(f"Verified user {self.addr}!")
                clients_data_lock.acquire()
                clients_data[self.client_socket] = {"user_id": self.user_id}
                clients_data_lock.release()
                self.client_socket.sendall("verified".encode())
        else:
            self.client_socket.sendall("invalid".encode())
    def get_chats(self):
        chats = self.db.get_user_chats(self.user_id)
        logger.debug(f"get_user_chats returned {chats}")
        logger.debug(f"User {self.addr} requested chat list, sending {len(chats) if chats else 0} chats")
        if chats is not None and len(chats) > 0:
            json_string = js.dumps(chats)
            chats_string = f"send_chats;{json_string}"
            self.client_socket.sendall(chats_string.encode())
            logger.debug(f"Sent chat list to {self.addr}: {chats_string}")
        else:
            self.client_socket.sendall("None".encode())
            logger.debug(f"No chats found for user {self.addr}, sent 'None'")
    def add_user_to_chat(self, chat_id, identifier):
        try:
            user_id = int(identifier)
            success = self.db.add_to_chat(chat_id, user_id)
        except ValueError:
            success = self.db.add_user_to_chat_by_username(chat_id, identifier)

        if success:
            self.client_socket.sendall("user_added".encode())
            logger.info(f"User {identifier} added to chat {chat_id}")
        else:
            self.client_socket.sendall("add_user_failed".encode())
            logger.error(f"Failed to add user {identifier} to chat {chat_id}")
    def remove_user_from_chat(self, chat_id, identifier):
        try:
            user_id = int(identifier)
            success = self.db.remove_from_chat(chat_id, user_id)
        except ValueError:
            success = self.db.remove_user_from_chat_by_username(chat_id, identifier)

        if success:
            self.client_socket.sendall("user_removed".encode())
            logger.info(f"User {identifier} removed from chat {chat_id}")
        else:
            self.client_socket.sendall("remove_user_failed".encode())
            logger.error(f"Failed to remove user {identifier} from chat {chat_id}")
    def get_messages(self, chat_id, limit, offset):
        messages = self.db.get_messages(chat_id, limit, offset)
        json_messages = js.dumps(messages)
        self.client_socket.sendall(f"messages;{json_messages}".encode())
    def send_message(self, chat_id, message_content):
        try:
            self.db.save_message(self.user_id, chat_id, message_content)
            self.client_socket.sendall("message_saved".encode())
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Nachricht: {e}")
            self.client_socket.sendall("message_save_failed".encode())
    def new_chat(self, chat_name):
        logger.debug(f"User {self.addr} requested new chat creation with name '{chat_name}'")
        chat_id = self.db.new_chat(self.user_id)
        if chat_id is not None:
            logger.debug(f"Chat '{chat_name}' mit ID {chat_id} erfolgreich für UserID: {self.user_id} erstellt")
            self.client_socket.sendall(f"chat_created;{chat_id}".encode())
            logger.debug(f"UserID: {self.user_id} erfolgreich zum Chat '{chat_name}' hinzugefügt")
        else:
            self.client_socket.sendall("chat_creation_failed".encode())
            logger.error(f"Fehler bei der Erstellung des Chats '{chat_name}' für {self.addr}")            

def INIT():
    global logger
    logging.basicConfig(level="DEBUG", format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

def init_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    logger.info(f"Server lauscht auf {host}:{port}")
    return server_socket



def main():
    INIT()
    server_socket = init_server("localhost", SERVER_PORT)
    while True:
        client_socket, addr = server_socket.accept()
        client_handler = ClientHandler(client_socket, addr)
        client_handler.start()
    
if __name__ == "__main__":
    main()

