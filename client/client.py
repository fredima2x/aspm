#! /bin/python
import socket
import threading
import time
import json as js

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
    time.sleep(1)

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
    
    # Wait for verification response
    response = client_socket.recv(1024).decode()
    if response == "verified":
        print("Login successful!")
    elif response == "invalid":
        print("Login failed!")
        client_socket.close()
        return None
    else:
        print(f"Unexpected response: {response}")
    
    return client_socket

def prompt(client_socket):
    current_chat_id = None
    while True:
        user_input = input("Enter command: ")
        if user_input == "exit":
            print("Exiting...")
            break
        if user_input == "help":
            print("Available commands: exit, help, list_chats, new_chat <name>, select_chat <id>, send_msg <message>, view_messages, add_user <id/username>, remove_user <id/username>")
            continue
        if user_input == "list_chats":
            print("Listing chats...")
            client_socket.sendall("get_chats".encode())
            response = client_socket.recv(4096).decode()
            if response.startswith("send_chats;"):
                chats_json = response[11:]  # Remove "send_chats;" prefix
                chats = js.loads(chats_json)
                print("Your chats:")
                for chat in chats:
                    print(f"- [ID: {chat['chat_id']}] Created at {chat['created_at']}")
            elif response == "None":
                print("No chats found.")
            else:
                print(f"Error: {response}")
            continue
        if user_input.startswith("new_chat"):
            input_parts = user_input.split(" ", 1)
            if len(input_parts) < 2:
                print("Usage: new_chat <name>")
                continue
            name = input_parts[1]
            print("Creating new chat...")
            client_socket.sendall(f"new_chat;{name}".encode())
            time.sleep(0.5)
            response = client_socket.recv(1024).decode()
            if response.startswith("chat_created"):
                print("Chat created successfully!")
            else:
                print("Failed to create chat.")
            continue
        if user_input.startswith("select_chat"):
            input_parts = user_input.split(" ")
            if len(input_parts) < 2:
                print("Usage: select_chat <chat_id>")
                continue
            try:
                current_chat_id = int(input_parts[1])
                print(f"Selected chat {current_chat_id}")
            except ValueError:
                print("Invalid chat ID")
            continue
        if user_input.startswith("send_msg"):
            if current_chat_id is None:
                print("Please select a chat first using 'select_chat <id>'")
                continue
            input_parts = user_input.split(" ", 1)
            if len(input_parts) < 2:
                print("Usage: send_msg <message>")
                continue
            message = input_parts[1]
            client_socket.sendall(f"send_message;{current_chat_id};{message}".encode())
            time.sleep(0.5)
            response = client_socket.recv(1024).decode()
            print(f"Server response: {response}")
            continue
        if user_input == "view_messages":
            if current_chat_id is None:
                print("Please select a chat first using 'select_chat <id>'")
                continue
            client_socket.sendall(f"get_messages;{current_chat_id}".encode())
            response = client_socket.recv(4096).decode()
            print("Messages in this chat:")
            print(response)
        if user_input.startswith("add_user"):
            if current_chat_id is None:
                print("Please select a chat first using 'select_chat <id>'")
                continue
            input_parts = user_input.split(" ", 1)
            if len(input_parts) < 2:
                print("Usage: add_user <username or user_id>")
                continue
            identifier = input_parts[1]
            client_socket.sendall(f"add_user_to_chat;{current_chat_id};{identifier}".encode())
            time.sleep(0.5)
            response = client_socket.recv(1024).decode()
            print(f"Server response: {response}")
            continue
        if user_input.startswith("remove_user"):
            if current_chat_id is None:
                print("Please select a chat first using 'select_chat <id>'")
                continue
            input_parts = user_input.split(" ", 1)
            if len(input_parts) < 2:
                print("Usage: remove_user <username or user_id>")
                continue
            identifier = input_parts[1]
            client_socket.sendall(f"remove_user_from_chat;{current_chat_id};{identifier}".encode())
            time.sleep(0.5)
            response = client_socket.recv(1024).decode()
            print(f"Server response: {response}")
            continue


def main():
    client_socket = connect_to_server(SERVER_HOST, SERVER_PORT)
    prompt(client_socket)

if __name__ == "__main__":
    main()    