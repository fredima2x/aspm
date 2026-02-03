import socket
import threading

### Configuration ###

ANTI_SPAM_MESSAGE = "Bitte senden Sie keine doppelten Nachrichten."
WELCOME_MESSAGE = "Willkommen auf dem Server!"

### end Configuration ###

clients = []  
clients_lock = threading.Lock()  

def init_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server lauscht auf {host}:{port}")
    return server_socket

def handle_client(client_socket, addr):
    global clients
    global clients_lock
    print(f"Verbindung von {addr} akzeptiert")
    
    client_socket.sendall(WELCOME_MESSAGE.encode())
    clients.append(client_socket)
    last_message = ""
    while True:
        data = client_socket.recv(1024)
        if last_message == data:
            client_socket.sendall(ANTI_SPAM_MESSAGE.encode())
            continue
        else: 
            last_message = data

        if not data:
            break

        message = data.decode()
        print(f"[{addr}]: {message}")

        for client in clients:
            if client != client_socket:
                client.send(data)

    clients.remove(client_socket)
    print(f"Verbindung von {addr} geschlossen!")
    client_socket.close()

def main():
    server_socket = init_server("localhost", 8080)
    while True:
        client_socket, addr = server_socket.accept()
        
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()
    
if __name__ == "__main__":
    main()