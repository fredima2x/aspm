#!/bin/python
import socket
import threading
import logging
import datasm

VERSION = "1.6.0"

SERVER_PORT = 8080          # Standard Port: 8080

# Lists:
clients = []  
clients_lock = threading.Lock()  
clients_data = {}  # Dictionary to store client-specific data, e.g., user_id
clients_data_lock = threading.Lock()  # Lock for synchronizing access to clients_data

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

def handle_client(client_socket, addr):
    global clients
    global clients_lock
    current_chat = None
    logger.info(f"Verbindung von {addr} akzeptiert")
    clients_lock.acquire()
    clients.append(client_socket)
    clients_lock.release()
    verified_user = False
    db = datasm.DatabaseManager()

    while True:
        try:
            data = client_socket.recv(1024)
        except OSError as e:
            logger.error(f"Socket-Fehler bei Client {addr}: {e}")
            break
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei Client {addr}: {e}")
            break
            
        if not data:
            break

        message = data.decode()
        ready_message = message.split(";")

        ### Block for unverified commands:
        if ready_message[0] == "send_creds":
            logger.info("Got send_creds Request!")
            username = ready_message[1]
            password = ready_message[2]
            logger.debug(f"password: {password}, username: {username}")
            if username != None and password != None:
                verify_status = db.verify_user(username, password)
                if verify_status == None:
                    client_socket.sendall("invalid".encode())
                    print(f"Wrong Creds! {addr}")
                else:
                    user_id = verify_status
                    verified_user = True
                    print(f"Verified user {addr}!")
                    clients_data_lock.acquire()
                    clients_data[client_socket] = {"user_id": user_id}
                    clients_data_lock.release()
                    client_socket.sendall("verified".encode())
            else:
                client_socket.sendall("invalid")
        if ready_message[0] == "send_newuser":
            logger.info("Got send_newuser Request!")
            username = ready_message[1]
            password = ready_message[2]
            if username != None and password != None:
                db.create_user(username, password)
            else:
                client_socket.sendall("invalid_creds")

        ### Block for verified commands:
        if verified_user:
            if ready_message[0] == "get_chats":
                chats = db.get_user_chats(user_id)
                logger.debug(f"get_user_chats returned {chats}")
                logger.debug(f"User {addr} requested chat list, sending {len(chats)} chats")
                if chats is not None and len(chats) > 0:
                    chats_string = ";".join([f"{chat['chat_id']}:{chat['properties']}" for chat in chats])
                    client_socket.sendall(chats_string.encode())
                    logger.debug(f"Sent chat list to {addr}: {chats_string}")
                else:
                    client_socket.sendall("None".encode())
                    logger.debug(f"No chats found for user {addr}, sent 'None'")
            if ready_message[0] == "get_messages":
                chat_id = ready_message[1]
                messages = db.load_messages(chat_id)
                messages_string = ";".join([f"{message[0]}:{message[1]}" for message in messages])
                client_socket.sendall(messages_string.encode())
            if ready_message[0] == "send_message":
                chat_id = ready_message[1]
                message_content = ready_message[2]
                db.save_message(chat_id, user_id, message_content)
                members = db.get_chat_members(chat_id)
                if members != None:
                    for member in members:
                        clients_data_lock.acquire()
                        for sock, data in clients_data.items():
                            if data["user_id"] == member[0] and sock != client_socket:
                                try:
                                    sock.sendall(f"new_message;{chat_id}".encode())
                                except Exception as e:
                                    logger.error(f"Fehler beim Senden der Nachricht an {sock.getpeername()}: {e}")
                        clients_data_lock.release()
                else:
                    logger.error(f"Chat {chat_id} nicht gefunden für Nachricht von {addr}")
            if ready_message[0] == "new_chat":
                logger.debug(f"User {addr} requested new chat creation with name '{ready_message[1]}'")
                chat_name = ready_message[1]
                chat_id = db.new_chat(user_id)
                if chat_id is not None:
                    client_socket.sendall(f"chat_created".encode())
                    logger.debug(f"Chat '{chat_name}' mit ID {chat_id} erfolgreich für UserID: {user_id} erstellt")
                else:
                    client_socket.sendall("chat_creation_failed".encode())
                    logger.error(f"Fehler bei der Erstellung des Chats '{chat_name}' für {addr}")
                
                    

    clients_lock.acquire()
    clients.remove(client_socket)
    clients_data_lock.acquire()
    if client_socket in clients_data:
        del clients_data[client_socket]
    clients_data_lock.release()
    clients_lock.release() 
    logger.info(f"Verbindung von {addr} geschlossen!")
    client_socket.close()

def main():
    INIT()
    server_socket= init_server("localhost", SERVER_PORT)
    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()
    
if __name__ == "__main__":
    main()

