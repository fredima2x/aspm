#!/bin/python
import socket
import threading

VERSION = "1.3.6"

### Configuration ###
# Important:
SERVER_PORT = 8080          # Standard Port: 8080
VERIFIED_SERVER = True      # Wenn True, müssen sich Benutzer mit Passwort anmelden oder registrieren
OPERATOR_USERNAME = "admin" # Benutzername für Operator-Befehle (z.B. Kick, Ban) 
OPERATOR_PASSWORD = "admin" # Passwort für Operator-Befehle (z.B. Kick, Ban)
ANTI_ALT_ACCOUNT = False    # Verhindert mehrere logins mit der gleichen IP-Addresse

# Non-important:
ANTI_SPAM_MESSAGE = "Bitte senden Sie keine doppelten Nachrichten."     # Hinweis bei Spam-Versuch
WELCOME_MESSAGE = f"Willkommen auf dem Server! (mcefli v{VERSION})"     # Willkommensnachricht
MAX_HISTORY_MESSAGES = 16                                               # Maximale Anzahl der Nachrichten, die beim Beitritt gesendet werden 

### end Configuration ###

# Lists:
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
    clients_lock.acquire()
    global clients
    clients_to_remove = []
    for client in clients:
        if client != client_socket:
            try:
                client[0].sendall(message.encode())
            except (OSError, BrokenPipeError, ConnectionResetError):
                clients_to_remove.append(client)
            except Exception:
                pass
    # Remove disconnected clients
    for client in clients_to_remove:
        try:
            clients.remove(client)
            print(f"Client {client[1]} wurde entfernt (Verbindung unterbrochen)")
        except ValueError:
            pass
    clients_lock.release()


def send_history(client_socket):
    global history
    global history_lock
    history_lock.acquire()
    history_to_send = history[-MAX_HISTORY_MESSAGES:]
    for msg in history_to_send:
        try:
            client_socket.sendall("\n".encode())
            client_socket.sendall(msg.encode())
        except (OSError, BrokenPipeError, ConnectionResetError):
            history_lock.release()
            return
    history_lock.release()

def handle_client(client_socket, addr):
    global clients
    global clients_lock
    global users
    global users_lock
    print(f"Verbindung von {addr} akzeptiert")
    
    try:
        encodet_username = client_socket.recv(1024)
        if not encodet_username:
            client_socket.close()
            return
        username = encodet_username.decode()
    except OSError as e:
        print(f"Fehler beim Empfangen vom Client {addr}: {e}")
        client_socket.close()
        return
    except Exception as e:
        print(f"Unerwarteter Fehler beim Empfangen vom Client {addr}: {e}")
        client_socket.close()
        return

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

    # Check Admin Status:
    if password == OPERATOR_PASSWORD and username == OPERATOR_USERNAME:
        IS_ADMIN = True
        client_socket.sendall("\n Warnung Administrator Account!".encode())
    else:
        IS_ADMIN = False

    sendall(f"\033[36m{username} hat den Chat betreten.\033[0m", client_socket)

    clients_lock.acquire()
    client_socket.sendall(WELCOME_MESSAGE.encode())
    clients.append((client_socket, username))
    clients_lock.release()
    last_message = ""

    send_history(client_socket)

    # Main loop
    while True:
        try:
            data = client_socket.recv(1024)
        except OSError as e:
            print(f"Socket-Fehler bei Client {addr}: {e}")
            break
        except Exception as e:
            print(f"Unerwarteter Fehler bei Client {addr}: {e}")
            break
            
        if not data:
            break
            
        if last_message == data:
            try:
                client_socket.sendall(ANTI_SPAM_MESSAGE.encode())
            except OSError:
                break
            continue
        else: 
            last_message = data
        
        # Check for commands starting with "/"
        if data.decode().startswith("/"):
            command = data.decode()[1:].split()[0]
            if command == "online":
                online_users_lock.acquire()
                online_list = ", ".join(online_users)
                online_users_lock.release()
                client_socket.sendall(f"Online Benutzer: {online_list}".encode())
                continue
        # Check for Admin commands starting with "!"
        if data.decode().startswith("!"):
            command = data.decode()[1:].split()[0]
            if IS_ADMIN:
                if command == "kick":
                    target_user = data.decode().split()[1]
                    online_users_lock.acquire()
                    if target_user in online_users:
                        online_users_lock.release()
                        clients_lock.acquire()
                        for c in clients:
                            if c[1] == target_user:
                                c[0].sendall("Sie wurden vom Server gekickt.".encode())
                                c[0].close()
                                clients.remove(c)
                                break
                        clients_lock.release()
                        sendall(f"\033[31m{target_user} wurde vom Server gekickt.\033[0m")       
            else:
                client_socket.sendall("Keine Berechtigung für Admin-Befehle.".encode())
                continue

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
    clients.remove((client_socket, username))
    clients_lock.release() 
    online_users_lock.acquire()
    online_users.remove(username)
    online_users_lock.release()
    print(f"Verbindung von {addr} geschlossen!")
    sendall(f"\033[36m{username} hat den Chat verlassen.\033[0m", client_socket)
    client_socket.close()

def main():
    server_socket = init_server("localhost", SERVER_PORT)
    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()
    
if __name__ == "__main__":
    main()

