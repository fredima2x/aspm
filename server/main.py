
VERSION = "1.12.1-8"
VERSION_SIMPLE = "1.12.1"
VERSIONS_COMPATIBILITY = {
    "1.12.1": ["1.12.1-8", "1.12.1-7", "1.12.1-6", "1.12.1-5", "1.12.1-4", "1.12.1-3", "1.12.1-2", "1.12.1-1"],
}

import socket
import subprocess
import sys
import threading
import logging
import messagesm
import ssl
import os
import json

# Lists:
clients = []  
clients_lock = threading.Lock()  
clients_data = {}  # Dictionary to store client-specific data, e.g., user_id
clients_data_lock = threading.Lock()  # Lock for synchronizing access to clients_data

def INIT():
    global logger
    logging.basicConfig(level="DEBUG", format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    load_config()  # Load configuration at startup
    configurate_server()  # Configure server based on loaded config

def load_config(path='config.json'):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config-Datei nicht gefunden: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Fehler in config.json: {e}")
        sys.exit(1)

def configurate_server():
    global ENCRYPTION_ENABLED, DNS_ENABLED, DNS_NAME, IP_ADDRESS, CERT_PATH, KEY_PATH, SERVER_PORT, VERSION, BIND_TO, CERT_SERVER_PORT

    config = load_config()
    VERSION             = config['VERSION']
    SERVER_PORT         = config['SERVER_PORT']
    ENCRYPTION_ENABLED  = config['ENCRYPTION_ENABLED']
    DNS_ENABLED         = config['DNS_ENABLED']
    DNS_NAME            = config['DNS_NAME']
    IP_ADDRESS          = config['IP_ADDRESS']
    CERT_PATH           = config['CERT_PATH']
    KEY_PATH            = config['KEY_PATH']
    BIND_TO             = config['BIND_TO']
    CERT_SERVER_PORT    = config['CERT_SERVER_PORT']

def certificate_matches_config():
    try:
        result = subprocess.run(
            ['openssl', 'x509', '-in', CERT_PATH, '-text', '-noout'],
            capture_output=True, text=True, check=True
        )
        output = result.stdout
        if DNS_ENABLED:
            return f"DNS:{DNS_NAME}" in output
        else:
            return f"IP Address:{IP_ADDRESS}" in output
    except Exception as e:
        logging.warning(f"Konnte Zertifikat nicht prüfen: {e}")
        return False

def ensure_certificates():
    global CERT_PATH, KEY_PATH
    cert_missing = not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH)
    cert_outdated = not cert_missing and not certificate_matches_config()
    if cert_missing or cert_outdated:
        try:
            if cert_outdated:
                logger.warning("Zertifikat passt nicht zur Config, erstelle neu...")
            else:
                logger.info("Zertifikat nicht gefunden, erstelle neu...")
            if DNS_ENABLED:
                SUBJ = f"/CN={DNS_NAME}"
                SAN = f"DNS:{DNS_NAME}"
            else:
                SUBJ = f"/CN={IP_ADDRESS}"
                SAN = f"IP:{IP_ADDRESS}"
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-keyout', KEY_PATH, '-out', CERT_PATH,
                '-days', '365', '-nodes',
                '-subj', SUBJ,
                '-addext', f'subjectAltName={SAN}'
            ], check=True, capture_output=True)
            logger.info("Zertifikat erstellt.")
        except Exception as e:
            logger.debug(f"Fehler beim Erstellen des Zertifikats: {e}")
            logger.info("Stelle sicher, dass OpenSSL installiert ist und im PATH liegt.")
            logger.info("Alternativ kannst du die Zertifikate manuell erstellen und im selben Verzeichnis ablegen.")
            logger.error("Breche ab.")
            sys.exit(1)

def serve_certificate(CERT_SERVER_PORT=8281):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', CERT_SERVER_PORT))
    sock.listen(5)
    while True:
        conn, _ = sock.accept()
        with open('cert.pem', 'rb') as f:
            conn.sendall(f.read())
        conn.close()

def init_server(host, port):
    if ENCRYPTION_ENABLED:
        ensure_certificates()
        threading.Thread(target=serve_certificate, daemon=True, args=(CERT_SERVER_PORT,)).start()
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((host, port))
    server_sock.listen(5)
    logger.info(f"Server lauscht auf {host}:{port}")
    return server_sock

def main():
    INIT()
    server_socket = init_server(BIND_TO, SERVER_PORT)
    while True:
        client_socket, addr = server_socket.accept()
        if ENCRYPTION_ENABLED:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)
            try:
                client_socket = context.wrap_socket(client_socket, server_side=True)
            except ssl.SSLError as e:
                logger.error(f"SSL handshake failed with {addr}: {e}")
                client_socket.close()
                continue
        client_handler = messagesm.ClientHandler(client_socket, addr, clients, clients_lock, clients_data, clients_data_lock)
        client_handler.start()
    
if __name__ == "__main__":
    main()

