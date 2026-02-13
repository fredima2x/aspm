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

def INIT():
    global logger
    logging.basicConfig(level="INFO")
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
            
            if ready_message[0] == "send_message":
                if current_chat == None:
                    client_socket.sendall("get_chat")
                else:
                    db.save_message(user_id, current_chat, ready_message[1], ready_message[2])
    


    clients_lock.acquire()
    clients.remove(client_socket)
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

