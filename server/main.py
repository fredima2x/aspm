#!/bin/python
import socket
import subprocess
import threading
import logging
import messagesm
import ssl
import os

VERSION = "1.8.2"

SERVER_PORT = 8080          # Standard Port: 8080

CERT_PATH = 'cert.pem'
KEY_PATH = 'key.pem'

# Lists:
clients = []  
clients_lock = threading.Lock()  
clients_data = {}  # Dictionary to store client-specific data, e.g., user_id
clients_data_lock = threading.Lock()  # Lock for synchronizing access to clients_data

def INIT():
    global logger
    logging.basicConfig(level="DEBUG", format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

def ensure_certificates():
    global CERT_PATH, KEY_PATH
    
    if not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH):
        try:
            print("Zertifikat nicht gefunden, erstelle neu...")
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-keyout', KEY_PATH, '-out', CERT_PATH,
                '-days', '365', '-nodes',
                '-subj', '/CN=127.0.0.1',
                '-addext', 'subjectAltName=IP:127.0.0.1'
            ], check=True)
            print("Zertifikat erstellt.")
        except Exception as e:
            print(f"Fehler beim Erstellen des Zertifikats: {e}")
            print("Stelle sicher, dass OpenSSL installiert ist und im PATH liegt.")
            print("Alternativ kannst du die Zertifikate manuell erstellen und im selben Verzeichnis ablegen.")
            print("Breche ab.")
            exit(1)

def serve_certificate(port=8081):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', port))
    sock.listen(5)
    while True:
        conn, _ = sock.accept()
        with open('cert.pem', 'rb') as f:
            conn.sendall(f.read())
        conn.close()

def init_server(host, port):
    ensure_certificates()
    threading.Thread(target=serve_certificate, daemon=True).start()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.bind((host, port))
    raw_sock.listen(5)
    logger.info(f"Server lauscht auf {host}:{port}")
    server_sock = context.wrap_socket(raw_sock, server_side=True)
    return server_sock

def main():
    INIT()
    server_socket = init_server("localhost", SERVER_PORT)
    while True:
        client_socket, addr = server_socket.accept()
        client_handler = messagesm.ClientHandler(client_socket, addr, clients, clients_lock, clients_data, clients_data_lock)
        client_handler.start()
    
if __name__ == "__main__":
    main()

