#! /bin/python
import socket
import threading
import time

# Client configuration
SERVER_HOST = "localhost"  # Server-Adresse (z.B. "localhost" oder "192.168.1.100")
SERVER_PORT = 8080         # Server-Port (muss mit dem Server übereinstimmen)

# DEBUG: DONT CHANGE THIS
GUI_ENABLED = False

def connect_to_server(host, port):
    global username
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    
    print("Delay...")
    time.sleep(5)

    #####
    if input("Create new Account (y/n)? ") == "y":
        sign_up = "send_newuser"
    else:
        sign_up = "send_creds"
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    #####

    creds = f"{sign_up};{username};{password}"

    client_socket.sendall(str(creds).encode())
    
    return client_socket

def prompt(client_socket):
    while True:
        user_input = input("Enter command: ")
        if user_input == "exit":
            print("Exiting...")
            break
        if user_input == "help":
            print("Available commands: exit, help, list_chats")
            continue
        if user_input == "list_chats":
            print("Listing chats...")
            client_socket.sendall("get_chats".encode())
            chats = client_socket.recv(1024).decode().split(";")
            print("Chats:")
            for chat in chats:
                print(f"- {chat}")
            continue
        if user_input.startswith("new_chat"):
            input_parts = user_input.split(" ")
            name = input_parts[1]
            print("Creating new chat...")
            client_socket.sendall(f"new_chat;{name}".encode())
            print("Delay...")
            time.sleep(1)
            response = client_socket.recv(1024).decode()
            if response.startswith("chat_created"):
                print("Chat created successfully!")
            else:
                print("Failed to create chat.")    
            continue


def main():
    client_socket = connect_to_server(SERVER_HOST, SERVER_PORT)
    prompt(client_socket)

if __name__ == "__main__":
    main()    