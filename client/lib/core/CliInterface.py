from client.lib.core.ServerConnection import ServerConnection
import logging

logging.basicConfig(level=logging.INFO)

def run_cli(server_host, server_port, cert_port):
    conn = ServerConnection.ServerConnection(server_host, server_port, cert_port)
    logging.info("Running in CLI mode.")
    while True:
        command = input("Enter command >>> ").strip().lower()
        if command == "list":
            print(conn.group_list())
        elif command == "signup":
            u = input("Enter username: ")
            p = input("Enter password: ")
            print(conn.verify_credentials(u, p, sign_up=True))
        elif command == "login":
            u = input("Enter username: ")
            p = input("Enter password: ")
            print(conn.verify_credentials(u, p, sign_up=False))
        elif command == "create":
            print(conn.group_create(input("Enter chat name: ")))
        elif command == "send":
            chat_id = input("Enter chat ID: ")
            msg = input("Enter message content: ")
            conn.message_new(chat_id, msg)
        elif command == "get":
             print(conn.message_getall(input("Enter chat ID: ")))
        elif command == "adduser":
            conn.group_useradd(input("Enter chat ID: "), input("Enter user: "))
        elif command == "rmuser":
            conn.group_userrm(input("Enter chat ID: "), input("Enter user: "))
        elif command == "delete_account":
            if input("Sicher? (yes/no): ").lower() == "yes":
                print(conn.delete_account())
        elif command == "delete_chat":
            chat_id = input("Enter chat ID: ")
            if input(f"Chat {chat_id} löschen? (yes/no): ").lower() == "yes":
                print(conn.delete_chat(chat_id))
        elif command == "delete_message":
            msg_id = input("Enter message ID: ")
            if input(f"Nachricht {msg_id} löschen? (yes/no): ").lower() == "yes":
                print(conn.delete_message(msg_id))
        elif command == "help":
            print("Befehle: list, create, send, get, adduser, rmuser, "
               "signup, login, delete_account, delete_chat, delete_message, quit")
        elif command == "quit":
            logging.info("Exiting.")
            conn.close()
            break
        else:
            logging.warning("Unbekannter Befehl.")