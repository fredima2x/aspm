#!/bin/python
import socket
import threading
import logging
import json as js
import messagesm

VERSION = "1.8.2"

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

def main():
    INIT()
    server_socket = init_server("localhost", SERVER_PORT)
    while True:
        client_socket, addr = server_socket.accept()
        client_handler = messagesm.ClientHandler(client_socket, addr, clients, clients_lock, clients_data, clients_data_lock)
        client_handler.start()
    
if __name__ == "__main__":
    main()

