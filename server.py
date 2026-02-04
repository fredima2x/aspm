#!/bin/python

from random import randint
import socket
import threading

VERSION = "1.3.5"

### Configuration ###

ANTI_SPAM_MESSAGE = "Bitte senden Sie keine doppelten Nachrichten."
WELCOME_MESSAGE = f"Willkommen auf dem Server! (mcefli v{VERSION})"
MAX_HISTORY_MESSAGES = 16
VERIFIED_SERVER = True

### end Configuration ###

users = []
users_lock = threading.Lock()
online_users = []
online_users_lock = threading.Lock()
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
    global history_lock
    history_lock.acquire()
    history_to_send = history[-MAX_HISTORY_MESSAGES:]
    for msg in history_to_send:
        client_socket.sendall("\n".encode())
        client_socket.sendall(msg.encode())
    history_lock.release()

def handle_client(client_socket, addr):
    global clients
    global clients_lock
    global users
    global users_lock
    print(f"Verbindung von {addr} akzeptiert")
    encodet_username = client_socket.recv(1024)
    username = encodet_username.decode()

    # Anti-double login
    online_users_lock.acquire()
    if username in online_users:
        client_socket.sendall("Benutzer bereits eingeloggt.".encode())
        online_users_lock.release()
        client_socket.close()
        return
    online_users_lock.release()

    # Authentifizierung
    if VERIFIED_SERVER == True:
        client_socket.sendall("get_password".encode())
        password = client_socket.recv(1024).decode()
        if (username, password) in users:
            pass
        elif username in [u[0] for u in users]:
            client_socket.sendall("Falsches Passwort!".encode())
            client_socket.close()
            return
        elif username not in [u[0] for u in users]:
            client_socket.sendall("Neuer Benutzer registriert.".encode()) 
    else:
        password = "no_password"

    # Add user to users list and online users list
    users_lock.acquire()
    users.append((username, password))
    users_lock.release()
    
    online_users_lock.acquire()
    online_users.append(username)
    online_users_lock.release()


    sendall(f"\033[36m{username} hat den Chat betreten.\033[0m", client_socket)

    clients_lock.acquire()
    client_socket.sendall(WELCOME_MESSAGE.encode())
    clients.append(client_socket)
    clients_lock.release()
    last_message = ""

    send_history(client_socket)

    # Main loop
    while True:
        data = client_socket.recv(1024)
        if last_message == data:
            client_socket.sendall(ANTI_SPAM_MESSAGE.encode())
            continue
        else: 
            last_message = data
        if not data:
            break

        # Wenn ein username in der Nachricht erwähnt wird, wird der username eingefährbt in magenta gesendet, sonst in weiß
        mentioned_users = [u for u in online_users if u in data.decode()]
        if username in mentioned_users:
            message = f"{username}: \033[35m{data.decode()}\033[0m"
        else:
            message = f"{username}: {data.decode()}"
    
        print(f"[{addr}]: {message}")
        history_lock.acquire()
        history.append(message)
        history_lock.release()
        sendall(message, client_socket)

    clients_lock.acquire()
    clients.remove(client_socket)
    clients_lock.release() 
    online_users_lock.acquire()
    online_users.remove(username)
    online_users_lock.release()
    print(f"Verbindung von {addr} geschlossen!")
    sendall(f"\033[36m{username} hat den Chat verlassen.\033[0m", client_socket)
    client_socket.close()

def main():
    server_socket = init_server("localhost", 8080)
    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()
    
if __name__ == "__main__":
    main()