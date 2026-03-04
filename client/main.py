#! /bin/python
import hashlib
import os
import socket
import sys
import time
import json as js
import logging
import ssl
from PyQt5.QtWidgets import (QApplication, QDialog, QMainWindow, QLabel, 
                              QVBoxLayout, QHBoxLayout, QSizePolicy,
                              QListWidgetItem, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5 import uic


# Client configuration
SERVER_HOST = "fredima.de"  # IP-Adresse des Servers
CERT_PATH = os.path.expanduser('~/.aspm_cert.pem')
SERVER_PORT = 8280
CERT_PORT = 8281
GUI_ENABLED = True  # Set to True if you have a GUI implementation

def INIT():
    global log
    logging.basicConfig(level="DEBUG", format='%(asctime)s - %(levelname)s - %(message)s')
    log = logging.getLogger(__name__)

class ServerConnection:
    def __init__(self, host, port):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.socket = None
        self.connect()
    
    def connect(self):
        try:
            try:
                fetch_certificate(self.host, self.port)  # Zertifikat einmalig vom Server holen
            except Exception as e:
                log.error(f"Failed to fetch certificate: {e}")
                exit(1)
            self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.context.load_verify_locations(CERT_PATH)
            self.raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = self.context.wrap_socket(self.raw_sock, server_hostname=self.host)
            self.socket.connect((self.host, self.port))
            self.logger.info(f"Connected to server at {self.host}:{self.port}")
        except ConnectionRefusedError:
            self.logger.error(f"Failed to connect to server at {self.host}:{self.port}")
            raise
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise
    
    def verify_credentials(self, username, password, sign_up=False):
        if not username or not password:
            self.logger.error("Username and password cannot be empty")
            return None
        
        sign_up_command = "send_newuser" if sign_up else "send_creds"
        creds = f"{sign_up_command};{username};{password}"
        try:
            self.socket.sendall(creds.encode())
            response = self.socket.recv(1024).decode()
            return response
        except Exception as e:
            self.logger.error(f"Error during credential verification: {e}")
            return None
    
    def group_list(self):
        self.logger.info("Listing chats...")
        try:
            self.socket.sendall("get_chats".encode())
            response = self.socket.recv(4096).decode()
            if response.startswith("send_chats;"):
                chats_json = response[11:]  # Remove "send_chats;" prefix
                chats = js.loads(chats_json)
                self.logger.info(f"Retrieved {len(chats)} chats")
                return chats
            elif response == "None":
                self.logger.info("No chats found.")
                return []
            else:
                self.logger.warning(f"Invalid Server Response: {response}")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving chat list: {e}")
            return None
    
    def group_create(self, name, properties="{}"):
        if not name:
            self.logger.error("Chat name cannot be empty")
            return False
        
        self.logger.info(f"Creating new chat: {name}")
        try:
            self.socket.sendall(f"new_chat;{name}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response.startswith("chat_created"):
                self.logger.info("Chat created successfully!")
                return True
            else:
                self.logger.error(f"Failed to create chat: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error creating chat: {e}")
            return False
    
    def message_new(self, chat, message_content, properties="{}"):
        if not chat or not message_content:
            self.logger.error("Chat ID and message content cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"send_message;{chat};{message_content}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "message_saved":
                self.logger.info("Message sent successfully")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return None
    
    def message_getall(self, chat, limit=100, offset=0):
        if not chat:
            self.logger.error("Chat ID cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"get_messages;{chat};{limit};{offset}".encode())
            time.sleep(0.1)
            response = self.socket.recv(4096).decode()
            if response.startswith("messages;"):
                json_response = response[9:]  # Remove "messages;" prefix
                messages = js.loads(json_response)
                self.logger.info(f"Retrieved {len(messages) if messages else 0} messages")
                return messages
            else:
                self.logger.warning(f"Invalid server response: {response}")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving messages: {e}")
            return None
    
    def group_useradd(self, chat, user):
        if not chat or not user:
            self.logger.error("Chat ID and user identifier cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"add_user_to_chat;{chat};{user}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "user_added":
                self.logger.info(f"User {user} added to chat {chat}")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error adding user to chat: {e}")
            return None
    
    def group_userrm(self, chat, user):
        if not chat or not user:
            self.logger.error("Chat ID and user identifier cannot be empty")
            return None
        
        try:
            self.socket.sendall(f"remove_user_from_chat;{chat};{user}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "user_removed":
                self.logger.info(f"User {user} removed from chat {chat}")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error removing user from chat: {e}")
            return None
    
    def delete_account(self):
        self.logger.info("Requesting account deletion...")
        try:
            self.socket.sendall("delete_account".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "account_deleted":
                self.logger.info("Account deleted successfully")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error deleting account: {e}")
            return None
    def delete_chat(self, chat_id=None):
        if not chat_id:
            self.logger.error("Chat ID cannot be empty")
            return None
        
        self.logger.info(f"Requesting deletion of chat {chat_id}...")
        try:
            self.socket.sendall(f"delete_chat;{chat_id}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "chat_deleted":
                self.logger.info(f"Chat {chat_id} deleted successfully")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error deleting chat: {e}")
            return None
    def delete_message(self, message_id=None):
        if not message_id:
            self.logger.error("Message ID cannot be empty")
            return None
        
        self.logger.info(f"Requesting deletion of message {message_id}...")

        try:
            self.socket.sendall(f"delete_message;{message_id}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response == "message_deleted":
                self.logger.info(f"Message {message_id} deleted successfully")
            else:
                self.logger.warning(f"Server response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error deleting message: {e}")
            return None

class LoginSignupDialog(QDialog):
    def __init__(self, conn):
        super().__init__()
        uic.loadUi("gui/gui_login.ui", self)
        self.conn = conn

        # Nach erfolgreichem Login/Signup speichern wir den Nutzernamen hier,
        # damit das Hauptfenster weiß wer eingeloggt ist.
        self.username = None
        
        # Buttons mit ihren Funktionen verbinden
        self.login_button.clicked.connect(self.try_login)
        self.signup_button.clicked.connect(self.try_signup)
        
        # Enter-Taste in den Passwortfeldern soll auch funktionieren
        self.enter_password_line_2.returnPressed.connect(self.try_login)
        self.repeat_password_line.returnPressed.connect(self.try_signup)
        
        # Wichtig: Passwortfelder als Passwortfelder konfigurieren.
        # Das wurde im Designer nicht gesetzt, also machen wir es hier.
        # QLineEdit.Password zeigt Punkte statt Klartext.
        from PyQt5.QtWidgets import QLineEdit
        self.enter_password_line_2.setEchoMode(QLineEdit.Password)
        self.enter_password_line.setEchoMode(QLineEdit.Password)
        self.repeat_password_line.setEchoMode(QLineEdit.Password)

    def try_login(self):
        username = self.enter_username_line_2.text().strip()
        password = self.enter_password_line_2.text()
        # Eingabevalidierung – beide Felder müssen ausgefüllt sein
        if not username or not password:
            QMessageBox.warning(self, "Fehler", "Bitte Benutzername und Passwort eingeben.")
            return
        stat = self.conn.verify_credentials(username, password, sign_up=False)
        if stat != "verified":
            QMessageBox.warning(self, "Fehler", "Ungültige Anmeldedaten. Bitte versuche es erneut.")
            # Passwortfeld leeren damit der Nutzer neu eingibt
            self.enter_password_line_2.clear()
            self.enter_password_line_2.setFocus()
            return
        self.username = username
        self.accept()  # Schließt den Dialog mit QDialog.Accepted

    def try_signup(self):
        username = self.enter_username_line.text().strip()
        password = self.enter_password_line.text()
        password_repeat = self.repeat_password_line.text()
        if not username or not password or not password_repeat:
            QMessageBox.warning(self, "Fehler", "Bitte alle Felder ausfüllen.")
            return
        if password != password_repeat:
            QMessageBox.warning(self, "Fehler", "Die Passwörter stimmen nicht überein.")
            self.enter_password_line.clear()
            self.repeat_password_line.clear()
            self.enter_password_line.setFocus()
            return
        
        stat = self.conn.verify_credentials(username, password, sign_up=True)
        if stat != "verified":
            QMessageBox.warning(self, "Fehler", f"Anmeldung fehlgeschlagen: {stat}")
            self.enter_password_line.clear()
            self.repeat_password_line.clear()
            self.enter_password_line.setFocus()        

        self.username = username
        self.accept()
class ChatWindow(QMainWindow):
    def __init__(self, username, conn):
        super().__init__()
        uic.loadUi("gui/gui.ui", self)
        self.conn = conn
        self.current_user = username

        # --- Chat-Datenstruktur ---
        # Jeder Chat hat einen Namen, eine Liste von Teilnehmern,
        # und eine Liste von Nachrichten (als Tupel: (text, received)).
        # So können wir beim Wechsel zwischen Chats den Verlauf wiederherstellen.
        self.chats = {}           # { chat_name: { "members": [...], "messages": [...] } }
        self.current_chat = None  # Der aktuell angezeigte Chat
        
        # --- ScrollArea vorbereiten ---
        # Das innere Widget der ScrollArea bekommt unser Layout.
        self.chat_layout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(8)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Signale verbinden ---
        self.send_button.clicked.connect(self.send_message)
        self.message_text.installEventFilter(self)
        
        self.addchat_button.clicked.connect(self.add_chat)
        self.rmchat_button.clicked.connect(self.remove_chat)
        self.adduser_button.clicked.connect(self.add_user)
        self.rmuser_button.clicked.connect(self.remove_user)
        
        # Wenn der Nutzer einen anderen Chat in der Liste anklickt
        self.listWidget.currentItemChanged.connect(self.switch_chat)
        
        # Einen Demo-Chat anlegen damit die App nicht leer startet
        self._create_chat("Allgemein", ["Alice", "Bob"])
        self.add_message("Willkommen im Chat!", received=True, chat="Allgemein")

    # -------------------------------------------------------------------------
    # Chat-Verwaltung
    # -------------------------------------------------------------------------

    def _create_chat(self, name, members=None):
        """Interne Hilfsmethode: legt einen Chat an und fügt ihn der Sidebar hinzu."""
        if name in self.chats:
            return  # Chat existiert bereits, nichts tun        
        self.chats[name] = {
            "members": members or [],
            "messages": []  # Wird beim Senden befüllt: [(text, received), ...]
        }
        
        # Eintrag in der QListWidget-Sidebar
        item = QListWidgetItem(name)
        self.listWidget.addItem(item)
        
        # Den neu erstellten Chat direkt auswählen
        self.listWidget.setCurrentItem(item)

    def add_chat(self):
        name, ok = QInputDialog.getText(self, "Neuer Chat", "Chat-Name:")
        if ok and name.strip():
            name = name.strip()

    def remove_chat(self):
        """Löscht den aktuell ausgewählten Chat."""
        if not self.current_chat:
            return
        
        confirm = QMessageBox.question(
            self, "Chat löschen", 
            f"Chat '{self.current_chat}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            # Aus der Datenstruktur entfernen
            del self.chats[self.current_chat]
            
            # Aus der Sidebar entfernen
            for i in range(self.listWidget.count()):
                if self.listWidget.item(i).text() == self.current_chat:
                    self.listWidget.takeItem(i)
                    break
            
            self.current_chat = None
            self._clear_chat_display()

    def switch_chat(self, current, previous):
        if not current:
            return
        
        # Nachrichten des aktuellen Chats speichern bevor wir wechseln –
        # das passiert automatisch, weil wir sie in self.chats[name]["messages"] ablegen.
        
        self.current_chat = current.text()
        self._clear_chat_display()
        
        messages_json = self.conn.message_getall(self.current_chat) 
        messages = js.loads(messages_json) if messages_json else []
        for msg in messages:
            text = msg.get("content", "")
            sender = msg.get("sender", "unknown")
            received = (sender != self.current_user)
            self._draw_bubble(f"{sender}: {text}", received)

    # -------------------------------------------------------------------------
    # Teilnehmer-Verwaltung
    # -------------------------------------------------------------------------

    def add_user(self):
        """Fügt einen Teilnehmer zum aktuellen Chat hinzu."""
        if not self.current_chat:
            QMessageBox.warning(self, "Kein Chat", "Bitte zuerst einen Chat auswählen.")
            return
        
        username, ok = QInputDialog.getText(self, "Nutzer hinzufügen", "Benutzername:")
        if ok and username.strip():
            username = username.strip()
            members = self.chats[self.current_chat]["members"]
            if username in members:
                QMessageBox.warning(self, "Fehler", f"'{username}' ist bereits im Chat.")
            else:
                members.append(username)
                # Systemnachricht im Chat anzeigen
                self.add_message(f"{username} ist dem Chat beigetreten.", received=True)

    def remove_user(self):
        """Entfernt einen Teilnehmer aus dem aktuellen Chat."""
        if not self.current_chat:
            return
        
        members = self.chats[self.current_chat]["members"]
        if not members:
            QMessageBox.information(self, "Leer", "Keine Teilnehmer im Chat.")
            return
        
        # Zeigt eine Auswahlliste aller Teilnehmer
        username, ok = QInputDialog.getItem(
            self, "Nutzer entfernen", "Teilnehmer wählen:", members, editable=False
        )
        if ok and username:
            members.remove(username)
            self.add_message(f"{username} hat den Chat verlassen.", received=True)

    # -------------------------------------------------------------------------
    # Nachrichten
    # -------------------------------------------------------------------------

    def add_message(self, text, received=False, chat=None):
        target_chat = chat or self.current_chat
        if not target_chat:
            return
        
        # In der Datenstruktur speichern (wichtig für den Chat-Wechsel)
        self.chats[target_chat]["messages"].append((text, received))
        
        # Nur zeichnen wenn dieser Chat gerade sichtbar ist
        if target_chat == self.current_chat:
            self._draw_bubble(text, received)

    def _draw_bubble(self, text, received):
        """Zeichnet eine einzelne Sprechblase in die ScrollArea."""
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(420)
        bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        
        if received:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #E5E5EA;
                    color: black;
                    border-radius: 18px;
                    padding: 10px 14px;
                    font-size: 14px;
                }
            """)
        else:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #0B93F6;
                    color: white;
                    border-radius: 18px;
                    padding: 10px 14px;
                    font-size: 14px;
                }
            """)
        
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if received:
            row.addWidget(bubble)
            row.addStretch()
        else:
            row.addStretch()
            row.addWidget(bubble)
        
        self.chat_layout.addLayout(row)
        
        # Verzögert nach unten scrollen, damit Qt das Layout erst berechnen kann
        QTimer.singleShot(50, lambda: self.message_area.verticalScrollBar().setValue(
            self.message_area.verticalScrollBar().maximum()
        ))

    def _clear_chat_display(self):
        """Leert die ScrollArea visuell, ohne Daten zu löschen."""
        # Alle Widgets und Layouts aus dem chat_layout entfernen
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.layout():
                # Verschachtelte Layouts (die Zeilen) müssen rekursiv geleert werden
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

    def send_message(self):
        text = self.message_text.toPlainText().strip()
        if text and self.current_chat:
            self.add_message(text, received=False)
            self.message_text.clear()

    def eventFilter(self, obj, event):
        if obj == self.message_text and event.type() == QEvent.KeyPress:
            # Enter sendet, Shift+Enter macht einen Zeilenumbruch
            if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    

    



def fetch_certificate(host, port=8280):
    if os.path.exists(CERT_PATH):
        return

    print(f"Erstes Verbinden – lade Zertifikat von {host}:{port}...")

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, port)) as raw_sock:
        with context.wrap_socket(raw_sock, server_hostname=host) as ssock:
            cert_der = ssock.getpeercert(binary_form=True)
            cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)

            fingerprint = hashlib.sha256(cert_der).hexdigest()
            fp_fmt = ":".join(fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2))

            with open(CERT_PATH, "w") as f:
                f.write(cert_pem)

            print(f"Zertifikat gespeichert unter {CERT_PATH}")
            print(f"WICHTIG: Bitte prüfe den Fingerprint beim Server:")
            print(f"sha256 Fingerprint={fp_fmt}")

def main():
    INIT()
    conn = ServerConnection(SERVER_HOST, SERVER_PORT)
    
    if GUI_ENABLED:
        app = QApplication(sys.argv)
        
        # Zuerst Login-Dialog öffnen und blockierend warten
        dialog = LoginSignupDialog(conn=conn)
        if dialog.exec_() != QDialog.Accepted:
            # Nutzer hat abgebrochen – App beenden ohne ChatWindow zu öffnen
            sys.exit(0)
        
        # Login war erfolgreich – wir wissen jetzt wer sich angemeldet hat
        username = dialog.username
        
        # Jetzt erst das Hauptfenster öffnen, mit dem Nutzernamen
        window = ChatWindow(username=username, conn=conn)
        window.show()
        sys.exit(app.exec_())

    else:
        log.info("Running in CLI mode. You can implement CLI interactions here.")
        while True:
            command = input("Enter command >>> ").strip().lower()
            if command == "list":
                chats = conn.group_list()
                print(chats)
            elif command == "signup":
                username = input("Enter username: ")
                password = input("Enter password: ")
                response = conn.verify_credentials(username, password, sign_up=True)
                print(response)
            elif command == "login":
                username = input("Enter username: ")
                password = input("Enter password: ")
                response = conn.verify_credentials(username, password, sign_up=False)
                print(response)
            elif command == "create":
                name = input("Enter chat name: ")
                conn.group_create(name)
            elif command == "send":
                chat_id = input("Enter chat ID: ")
                message = input("Enter message content: ")
                conn.message_new(chat_id, message)
            elif command == "get":
                chat_id = input("Enter chat ID: ")
                messages = conn.message_getall(chat_id)
                print(messages)
            elif command == "adduser":
                chat_id = input("Enter chat ID: ")
                user = input("Enter user identifier to add: ")
                conn.group_useradd(chat_id, user)
            elif command == "rmuser":
                chat_id = input("Enter chat ID: ")
                user = input("Enter user identifier to remove: ")
                conn.group_userrm(chat_id, user)
            elif command == "delete_account":
                confirmation = input("Are you sure you want to delete your account? This action cannot be undone. (yes/no): ")
                if confirmation.lower() == "yes":
                    conn.delete_account()
                else:
                    log.info("Account deletion cancelled.")
            elif command == "delete_chat":
                chat_id = input("Enter chat ID to delete: ")
                confirmation = input(f"Are you sure you want to delete chat {chat_id}? This action cannot be undone. (yes/no): ")
                if confirmation.lower() == "yes":
                    conn.delete_chat(chat_id)
                else:
                    log.info("Chat deletion cancelled.")
            elif command == "delete_message":
                chat_id = input("Enter chat ID: ")
                message_id = input("Enter message ID to delete: ")
                confirmation = input(f"Are you sure you want to delete message {message_id} in chat {chat_id}? This action cannot be undone. (yes/no): ")
                if confirmation.lower() == "yes":
                    conn.delete_message(chat_id, message_id)
                else:
                    log.info("Message deletion cancelled.")
            elif command == "help":
                log.info("Available commands: list, create, send, get, adduser, rmuser, quit, signup, login, delete_account, delete_chat")
            elif command == "quit":
                log.info("Exiting client.")
                break
            else:
                log.warning("Unknown command. Please try again.")

if __name__ == "__main__":
    main()
