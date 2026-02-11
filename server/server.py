#!/bin/python
import socket
import threading
import logging
import database

VERSION = "1.6.0"

SERVER_PORT = 8080          # Standard Port: 8080

# Lists:
saves = []
saves_lock = threading.Lock()
sessions = []
sessions_lock = threading.Lock()
clients = []  
clients_lock = threading.Lock()  

def INIT():
    global logger
    logger = logging.getLogger(__name__)

def init_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    logger.info(f"Server lauscht auf {host}:{port}")
    return server_socket

def handle_data(data, client_socket):
    message = data.decode()

def handle_client(client_socket, addr):
    global clients
    global clients_lock
    logger.info(f"Verbindung von {addr} akzeptiert")
    
    clients_lock.acquire()
    clients.append(client_socket)
    clients_lock.release()

    # Main loop
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

        handle_data(data, client_socket)  

    clients_lock.acquire()
    clients.remove(client_socket)
    clients_lock.release() 
    logger.info(f"Verbindung von {addr} geschlossen!")
    client_socket.close()

def main():
    INIT()
    server_socket = init_server("localhost", SERVER_PORT)
    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()
    
if __name__ == "__main__":
    main()

