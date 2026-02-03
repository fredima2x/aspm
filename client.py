import socket
import threading

messages_lock = threading.Lock()

def connect_to_server(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    return client_socket

def send(client_socket):
    while True:
        message = input()
        if message.lower() == 'quit':
            client_socket.close()
            break
        client_socket.sendall(message.encode())

def receive_messages(client_socket):
    while True:
        response = client_socket.recv(1024)
        if not response:
            break
        print("Server:", response.decode())

def main():
    client_socket = connect_to_server("localhost", 8080)
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()
    send(client_socket)


if __name__ == "__main__":
    main()    