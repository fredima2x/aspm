
VERSION = "1.12.1-8"
VERSION_SIMPLE = "1.12.1"
VERSIONS_COMPATIBILITY = {
    "1.12.1": ["*"],
}

import socket
import threading
import json
import time
import logging

BINDING_HOST = "0.0.0.0"
BINDING_PORT = 8282

#----------------------
# EXPLANATION:
# Dieser Server Mirror dient dazu, die Serverinformationen (Host, Port) an die Clients zu verteilen.
# Der Mirror ist Hardcoded im Client hinterlegt, damit die Clients immer wissen, wo sie die Serverinformationen abrufen können, auch wenn sich die Serveradresse ändert.
# Angegeben sind:
# - Hostname des Servers (z.B. "fredima.de" oder "localhost")
# - Name des Servers (z.B. "neumann", "einstein")
# - Database, die der Server verwendet (z.B. "main")
# - Port für verschlüsselte Verbindungen (z.B. 8280)
# - Port für Zertifikatsanfragen (z.B. 8281)

servers = [
    ("192.168.178.138", "einstein", "main", 8280, 8281)
]
# ----------------------
servers_json = json.dumps(servers)

clients = []
clients_lock = threading.Lock()

def handle_client(client_socket, logger):
    clients_lock.acquire()
    clients.append(client_socket)
    clients_lock.release()

    for _ in range(10):
        try:
            client_socket.sendall(servers_json.encode())
        except Exception as e:
            logger.warning(f"Failed to send server info to client: {e}")
            break
        time.sleep(1)
    
    client_socket.close()
    clients_lock.acquire()
    clients.remove(client_socket)
    clients_lock.release()


def main():
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
    logger = logging.getLogger("ServerMirror")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((BINDING_HOST, BINDING_PORT))
    server_socket.listen(5)
    logger.info(f"Server Mirror listening on {BINDING_HOST}:{BINDING_PORT}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            logger.info(f"Accepted connection from {addr}")
            threading.Thread(target=handle_client, args=(client_socket, logger)).start()
    except KeyboardInterrupt:
        logger.info("Shutting down Server Mirror")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()    
