#! /bin/python

import socket
import threading

messages_lock = threading.Lock()

def start_session():
    print("Client-Session gestartet.")
    print("Geben Sie 'quit' ein, um die Sitzung zu beenden.")
    global username
    username = input("Geben Sie Ihren Benutzernamen ein: ")
    print(f"Willkommen, {username}!")

def connect_to_server(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    client_socket.sendall(username.encode())
    print("\n" + "-"*50)
    return client_socket

def send(client_socket):
    while True:
        inputs = input()
        message = inputs
        if inputs.lower() == 'quit':
            client_socket.close()
            break
        client_socket.sendall(message.encode())
        print(f"{username}> ", end='', flush=True)

def receive_messages(client_socket):
    while True:
        response = client_socket.recv(1024)
        if not response:
            break
        print("\r" + " " * 80 + "\r", end='')
        print(response.decode())
        print(f"{username}> ", end='', flush=True)

def main():
    start_session()
    client_socket = connect_to_server("localhost", 8080)
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()
    send(client_socket)

if __name__ == "__main__":
    main()    