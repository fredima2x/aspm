import socket
import threading

VERSION = "1.2.5"

### Configuration ###

ANTI_SPAM_MESSAGE = "Bitte senden Sie keine doppelten Nachrichten."
WELCOME_MESSAGE = f"Willkommen auf dem Server! (mcefli v{VERSION})"

### end Configuration ###

users = []
users_lock = threading.Lock()
clients = []  
clients_lock = threading.Lock()  

history = []
history_lock = threading.Lock()

def init_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server lauscht auf {host}:{port}")
    return server_socket

def sendall(message, client_socket=None):
    global clients
    for client in clients:
        if client != client_socket:
            client.sendall(message.encode())

def send_history(client_socket):
    global history
    history_lock.acquire()
    client_socket.sendall("his_start".encode())
    for msg in history:
        client_socket.sendall(msg.encode())
    client_socket.sendall("his_complete".encode())
    history_lock.release()

def handle_client(client_socket, addr):
    global clients
    global clients_lock
    global users
    global users_lock
    print(f"Verbindung von {addr} akzeptiert")
    encodet_username = client_socket.recv(1024)
    username = encodet_username.decode()
    users_lock.acquire()
    users.append(username)
    users_lock.release()
    sendall(f"{username} hat den Chat betreten.", client_socket)

    client_socket.sendall(WELCOME_MESSAGE.encode())
    clients.append(client_socket)
    last_message = ""

    while True:
        data = client_socket.recv(1024)
        if data == b"get_history":
            send_history(client_socket)
            continue
        if last_message == data:
            client_socket.sendall(ANTI_SPAM_MESSAGE.encode())
            continue
        else: 
            last_message = data
        if not data:
            break

        message = f"{username}: {data.decode()}"
        print(f"[{addr}]: {message}")
        history_lock.acquire()
        history.append(message)
        history_lock.release()
        sendall(message, client_socket)

    users_lock.acquire()
    users.remove(username)
    users_lock.release()
    clients.remove(client_socket)
    print(f"Verbindung von {addr} geschlossen!")
    sendall(f"{username} hat den Chat verlassen.", client_socket)
    client_socket.close()

def main():
    server_socket = init_server("localhost", 8080)
    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()
    
if __name__ == "__main__":
    main()