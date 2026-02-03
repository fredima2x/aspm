import socket
import threading

clients = []  # List to store connected client sockets
clients_lock = threading.Lock()  # Lock for thread-safe access to clients list

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
    welcome_message = "Willkommen auf dem Server!"
    client_socket.sendall(welcome_message.encode())
    with clients_lock:
        clients.append(client_socket)  # Add new client to the list
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode()
            print(f"[{addr}]: {message}")
            with clients_lock:
                for client in clients:
                    try:
                        client.sendall(data)
                    except Exception as e:
                        print(f"Error sending message to {client}: {e}")
    finally:
        with clients_lock:
            clients.remove(client_socket)  # Remove client from the list upon disconnect
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