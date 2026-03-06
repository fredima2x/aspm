#! /bin/python
import hashlib
import os
import socket
import sys
import time
import json as js
import logging
import ssl

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QLabel,
    QVBoxLayout, QHBoxLayout, QSizePolicy,
    QListWidgetItem, QInputDialog, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5 import uic

USERNAME = None
PASSWORD = None
USERID   = None
cert_port = None
server_port = None
server_host = None
servers = None



# ─────────────────────────────────────────────────────────────────────────────
#  Konfiguration
# ─────────────────────────────────────────────────────────────────────────────
MIRROR_SERVER_HOST = "localhost"
MIRROR_SERVER_PORT = 8282
CERT_PATH   = os.path.expanduser("~/.aspm_cert.pem")
GUI_ENABLED = True


# ─────────────────────────────────────────────────────────────────────────────
#  Logging
# ─────────────────────────────────────────────────────────────────────────────
def INIT():
    global log
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    log = logging.getLogger(__name__)

def get_server_info():
    global servers
    """Fragt den Server Mirror nach verfügbaren Servern und gibt die erste gültige Antwort zurück."""
    try:
        with socket.create_connection((MIRROR_SERVER_HOST, MIRROR_SERVER_PORT), timeout=5) as sock:
            data = sock.recv(4096).decode()
            servers = js.loads(data)
            log.info(f"Empfangene Serverinformationen: {servers}")
    except Exception as e:
        log.error(f"Fehler beim Abrufen der Serverinformationen: {e}")
    # "with" block handles socket closing automatically; no finally block needed
    return None


def resource_path(relative_path):
    """Gibt den korrekten Pfad zurück – im Dev-Modus und nach PyInstaller-Build."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller-Build: Dateien sind in einem temp-Ordner entpackt
        base_path = sys._MEIPASS
    else:
        # Normaler Dev-Modus
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# ─────────────────────────────────────────────────────────────────────────────
#  Zertifikat
# ─────────────────────────────────────────────────────────────────────────────
def fetch_certificate(host, port=cert_port):
    if os.path.exists(CERT_PATH):
        return
    print(f"Erstes Verbinden – lade Zertifikat von {host}:{port} ...")
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            cert_pem = sock.recv(8192).decode()
            with open(CERT_PATH, "w") as f:
                f.write(cert_pem)
        print(f"Zertifikat gespeichert: {CERT_PATH}")
    except Exception as e:
        log.error(f"Fehler beim Abrufen des Zertifikats: {e}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
#  Server-API
# ─────────────────────────────────────────────────────────────────────────────
class ServerConnection:
    def __init__(self, host, port):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.socket = None
        try:
            self.connect()
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {e}")
    
    def connect(self):
        try:
            fetch_certificate(server_host, cert_port)
        except Exception as e:
            log.error(f"Failed to fetch certificate: {e}")
            exit(1)
        try:
            self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.context.load_verify_locations(CERT_PATH)
            self.raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = self.context.wrap_socket(self.raw_sock, server_hostname=self.host)
            self.socket.connect((self.host, self.port))
            self.logger.info(f"Connected to server at {self.host}:{self.port}")
        except ConnectionRefusedError:
            self.logger.error(f"Failed to connect to server at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Connection error: {e}")

    def close(self):
        if self.socket:
            self.socket.close()
            self.logger.info("Connection closed")

    def status(self):
        if self.socket and self.socket.fileno() != -1:
            return True
        return False
        
    def verify_credentials(self, username, password, sign_up=False):
        if not username or not password:
            self.logger.error("Username and password cannot be empty")
            return None
        cmd = "send_newuser" if sign_up else "send_creds"
        try:
            self.socket.sendall(f"{cmd};{username};{password}".encode())
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error during credential verification: {e}")
            return None

    def group_list(self):
        # Returns: [{"chat_id":1,"creator_id":1,"members":[1,2],...}, ...]
        self.logger.info("Listing chats...")
        try:
            self.socket.sendall("get_chats".encode())
            response = self.socket.recv(4096).decode()
            if response.startswith("send_chats;"):
                chats = js.loads(response[11:])
                self.logger.info(f"Retrieved {len(chats)} chats")
                return chats
            elif response == "None":
                return []
            self.logger.warning(f"Invalid Server Response: {response}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving chat list: {e}")
            return None

    def group_create(self, name, properties="{}"):
        if not name:
            return False
        self.logger.info(f"Creating new chat: {name}")
        try:
            self.socket.sendall(f"new_chat;{name}".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response.startswith("chat_created"):
                self.logger.info("Chat created successfully!")
                return True
            self.logger.error(f"Failed to create chat: {response}")
            return False
        except Exception as e:
            self.logger.error(f"Error creating chat: {e}")
            return False

    def message_new(self, chat, message_content, properties="{}"):
        if not chat or not message_content:
            return None
        try:
            self.socket.sendall(f"send_message;{chat};{message_content}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return None

    def message_getall(self, chat, limit=100, offset=0):
        # Returns: [{"message_id":1,"sender_id":2,"content":"...","send_at":"..."}, ...]
        # Newest message first!
        if not chat:
            return None
        try:
            self.socket.sendall(f"get_messages;{chat};{limit};{offset}".encode())
            time.sleep(0.1)
            response = self.socket.recv(4096).decode()
            if response.startswith("messages;"):
                messages = js.loads(response[9:])
                self.logger.info(f"Retrieved {len(messages) if messages else 0} messages")
                return messages
            self.logger.warning(f"Invalid server response: {response}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving messages: {e}")
            return None

    def group_useradd(self, chat, user):
        if not chat or not user:
            return None
        try:
            self.socket.sendall(f"add_user_to_chat;{chat};{user}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error adding user: {e}")
            return None

    def group_userrm(self, chat, user):
        if not chat or not user:
            return None
        try:
            self.socket.sendall(f"remove_user_from_chat;{chat};{user}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error removing user: {e}")
            return None

    def delete_account(self):
        try:
            self.socket.sendall("delete_account".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error deleting account: {e}")
            return None

    def delete_chat(self, chat_id=None):
        if not chat_id:
            return None
        try:
            self.socket.sendall(f"delete_chat;{chat_id}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error deleting chat: {e}")
            return None

    def delete_message(self, message_id=None):
        if not message_id:
            return None
        try:
            self.socket.sendall(f"delete_message;{message_id}".encode())
            time.sleep(0.1)
            return self.socket.recv(1024).decode()
        except Exception as e:
            self.logger.error(f"Error deleting message: {e}")
            return None
    
    def get_myuser_id(self):
        try:
            self.socket.sendall(f"get_user_id".encode())
            time.sleep(0.1)
            response = self.socket.recv(1024).decode()
            if response.startswith("user_id;"):
                user_id = int(response[8:])
                self.logger.info(f"User ID for is {user_id}")
                return user_id
            self.logger.warning(f"Invalid server response: {response}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving user ID: {e}")
            return None

# ─────────────────────────────────────────────────────────────────────────────
#  Login / Signup Dialog
# ─────────────────────────────────────────────────────────────────────────────
class LoginSignupDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(resource_path("assets/dep_login.ui"), self)
        self.conn = ServerConnection(server_host, server_port)
        self.username = None  # Gesetzt nach erfolgreichem Login/Signup

        # Passwortfelder maskieren
        self.enter_password_line_2.setEchoMode(QLineEdit.Password)  # Login-Tab
        self.enter_password_line.setEchoMode(QLineEdit.Password)    # Signup-Tab
        self.repeat_password_line.setEchoMode(QLineEdit.Password)   # Signup Wiederholung

        # Signale
        self.login_button.clicked.connect(self.try_login)
        self.signup_button.clicked.connect(self.try_signup)
        self.enter_password_line_2.returnPressed.connect(self.try_login)
        self.repeat_password_line.returnPressed.connect(self.try_signup)

    def try_login(self):
        global USERNAME, PASSWORD, USERID
        username = self.enter_username_line_2.text().strip()
        password = self.enter_password_line_2.text()

        if not username or not password:
            QMessageBox.warning(self, "Fehler", "Bitte Benutzername und Passwort eingeben.")
            return

        response = self.conn.verify_credentials(username, password, sign_up=False)
        if response == "verified":
            USERNAME = username
            PASSWORD = password
            USERID = self.conn.get_myuser_id()
            self.username = username
            self.conn.close()
            self.accept()
        else:
            QMessageBox.warning(self, "Login fehlgeschlagen",
                                f"Ungültige Anmeldedaten.\nServer: {response}")
            self.enter_password_line_2.clear()
            self.enter_password_line_2.setFocus()

    def try_signup(self):
        global USERNAME, PASSWORD, USERID
        username      = self.enter_username_line.text().strip()
        password      = self.enter_password_line.text()
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

        response = self.conn.verify_credentials(username, password, sign_up=True)
        if response == "verified":
            USERNAME = username
            PASSWORD = password
            USERID = self.conn.get_myuser_id()
            self.username = username
            self.conn.close()  # Neue Verbindung im ChatWindow mit gültigen Credentials
            self.accept()
        else:
            # BUG FIX: Vorher wurde accept() auch bei Fehler aufgerufen
            QMessageBox.warning(self, "Registrierung fehlgeschlagen", f"Server: {response}")
            self.enter_password_line.clear()
            self.repeat_password_line.clear()
            self.enter_password_line.setFocus()


# ─────────────────────────────────────────────────────────────────────────────
#  Chat-Hauptfenster
# ─────────────────────────────────────────────────────────────────────────────
class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            log.info("ChatWindow: Lade UI...")
            uic.loadUi(resource_path("assets/dep_gui.ui"), self)
            log.info("ChatWindow: UI geladen")
        except Exception as e:
            log.error(f"ChatWindow: Fehler beim Laden der UI: {e}", exc_info=True)
            raise

        try:
            log.info("ChatWindow: Verbinde zum Server...")
            self.conn = ServerConnection(server_host, server_port)
            log.info("ChatWindow: Mit Server verbunden")
        except Exception as e:
            log.error(f"ChatWindow: Fehler beim Verbinden: {e}", exc_info=True)
            raise

        self.username = USERNAME
        self.password = PASSWORD
        self.user_id = USERID

        # verify
        if not self.conn.status():
            log.error("ChatWindow: Verbindung zum Server fehlgeschlagen.")
            QMessageBox.critical(self, "Fehler", "Verbindung zum Server fehlgeschlagen.")
            sys.exit(1)

        try:
            self.conn.verify_credentials(self.username, self.password)
            self.my_sender_id = self.conn.get_myuser_id()
            log.info(f"ChatWindow: Benutzer-ID ist {self.my_sender_id}")
        except Exception as e:
            log.error(f"ChatWindow: Fehler bei der Verifizierungsanfrage: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", "Fehler bei der Verifizierungsanfrage.")
            sys.exit(1)


        self.current_chat_id   = None
        self.last_message_id   = None

        try:
            log.info("ChatWindow: Richte ScrollArea ein...")
            self.chat_layout = QVBoxLayout(self.scrollAreaWidgetContents)
            self.chat_layout.setAlignment(Qt.AlignTop)
            self.chat_layout.setSpacing(8)
            self.chat_layout.setContentsMargins(10, 10, 10, 10)
            log.info("ChatWindow: ScrollArea eingerichtet")
        except Exception as e:
            log.error(f"ChatWindow: Fehler beim Einrichten der ScrollArea: {e}", exc_info=True)
            raise

        self.setWindowTitle(f"ASPM – {self.username}")

        try:
            log.info("ChatWindow: Verbinde Signale...")
            self.send_button.clicked.connect(self.send_message)
            self.message_text.installEventFilter(self)
            self.addchat_button.clicked.connect(self.add_chat)
            self.rmchat_button.clicked.connect(self.remove_chat)
            self.adduser_button.clicked.connect(self.add_user)
            self.rmuser_button.clicked.connect(self.remove_user)
            self.listWidget.currentItemChanged.connect(self.switch_chat)
            log.info("ChatWindow: Signale verbunden")
        except Exception as e:
            log.error(f"ChatWindow: Fehler beim Verbinden der Signale: {e}", exc_info=True)
            raise

        try:
            log.info("ChatWindow: Lade Chatliste...")
            self.load_chat_list()
            log.info("ChatWindow: Chatliste geladen")
        except Exception as e:
            log.error(f"ChatWindow: Fehler beim Laden der Chatliste: {e}", exc_info=True)
            raise

        try:
            log.info("ChatWindow: Starte Timer...")
            self.msg_timer = QTimer(self)
            self.msg_timer.setInterval(3000)
            self.msg_timer.timeout.connect(self._poll_messages)
            self.msg_timer.start()

            self.chat_timer = QTimer(self)
            self.chat_timer.setInterval(30000)
            self.chat_timer.timeout.connect(self.load_chat_list)
            self.chat_timer.start()
            log.info("ChatWindow: Timer gestartet")
        except Exception as e:
            log.error(f"ChatWindow: Fehler beim Starten der Timer: {e}", exc_info=True)
            raise

        log.info("ChatWindow: Initialisierung abgeschlossen")

    # ── Chatliste ──────────────────────────────────────────────────────────

    def load_chat_list(self):
        """Lädt alle Chats vom Server und füllt die Sidebar."""
        chats = self.conn.group_list()
        if chats is None:
            QMessageBox.warning(self, "Fehler", "Chatliste konnte nicht geladen werden.")
            return

        previously_selected_id = self.current_chat_id

        # blockSignals verhindert dass switch_chat für jeden addItem feuert
        self.listWidget.blockSignals(True)
        self.listWidget.clear()

        for chat in chats:
            # Server: {"chat_id":1, "creator_id":1, "members":[1,2], ...}
            # Kein Name vorhanden → Chat #ID anzeigen
            chat_id      = chat["chat_id"]
            member_count = len(chat.get("members", []))
            item = QListWidgetItem(f"Chat #{chat_id}  ({member_count} Mitglieder)")
            item.setData(Qt.UserRole, chat_id)
            self.listWidget.addItem(item)

            if chat_id == previously_selected_id:
                self.listWidget.setCurrentItem(item)

        self.listWidget.blockSignals(False)

        # Falls nichts ausgewählt, erstes Element wählen
        if self.listWidget.currentItem() is None and self.listWidget.count() > 0:
            self.listWidget.setCurrentRow(0)

    # ── Chat-Verwaltung ────────────────────────────────────────────────────

    def add_chat(self):
        name, ok = QInputDialog.getText(self, "Neuer Chat", "Chat-Name:")
        if not ok or not name.strip():
            return
        success = self.conn.group_create(name.strip())
        if success:
            self.load_chat_list()
        else:
            QMessageBox.warning(self, "Fehler", "Chat konnte nicht erstellt werden.")

    def remove_chat(self):
        if not self.current_chat_id:
            QMessageBox.warning(self, "Kein Chat", "Bitte zuerst einen Chat auswählen.")
            return
        confirm = QMessageBox.question(
            self, "Chat löschen",
            f"Chat #{self.current_chat_id} wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        response = self.conn.delete_chat(self.current_chat_id)
        if response == "chat_deleted":
            self.current_chat_id = None
            self._clear_chat_display()
            self.load_chat_list()
        else:
            QMessageBox.warning(self, "Fehler", f"Löschen fehlgeschlagen.\nServer: {response}")

    def switch_chat(self, current, previous):
        if not current:
            return
        self.current_chat_id = current.data(Qt.UserRole)
        self.last_message_id = None  # Reset damit load_messages alles neu lädt
        self._clear_chat_display()
        
        messages_json = self.conn.get_messages(self.current_chat) 
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
        if not self.current_chat_id:
            QMessageBox.warning(self, "Kein Chat", "Bitte zuerst einen Chat auswählen.")
            return
        username, ok = QInputDialog.getText(self, "Nutzer hinzufügen", "Benutzername:")
        if not ok or not username.strip():
            return
        response = self.conn.group_useradd(self.current_chat_id, username.strip())
        if response == "user_added":
            self._draw_system_message(f"{username.strip()} ist dem Chat beigetreten.")
            self.load_chat_list()  # Mitgliederzahl in Sidebar aktualisieren
        else:
            QMessageBox.warning(self, "Fehler",
                                f"'{username}' konnte nicht hinzugefügt werden.\nServer: {response}")

    def remove_user(self):
        if not self.current_chat_id:
            QMessageBox.warning(self, "Kein Chat", "Bitte zuerst einen Chat auswählen.")
            return
        username, ok = QInputDialog.getText(self, "Nutzer entfernen", "Benutzername:")
        if not ok or not username.strip():
            return
        response = self.conn.group_userrm(self.current_chat_id, username.strip())
        if response == "user_removed":
            self._draw_system_message(f"{username.strip()} hat den Chat verlassen.")
            self.load_chat_list()  # Mitgliederzahl in Sidebar aktualisieren
        else:
            QMessageBox.warning(self, "Fehler",
                                f"'{username}' konnte nicht entfernt werden.\nServer: {response}")

    # ── UI-Hilfsmethoden ───────────────────────────────────────────────────

    def _draw_bubble(self, text, received, timestamp=""):
        """Zeichnet eine Sprechblase. Blau = eigene, Grau = fremde Nachricht."""
        display_text = text
        if timestamp:
            # Nur HH:MM anzeigen
            display_text = f"{text}"

        bubble = QLabel(display_text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(420)
        bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        if received:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #E5E5EA;
                    color: #1c1c1e;
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
        self._scroll_to_bottom()

    def _draw_system_message(self, text):
        """Zentrierte Systemnachricht (z.B. 'User X beigetreten')."""
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #8e8e93;
                font-size: 12px;
                padding: 4px 0px;
            }
        """)
        self.chat_layout.addWidget(label)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        # QTimer nötig: Qt berechnet das Layout erst im nächsten Frame
        QTimer.singleShot(50, lambda: self.message_area.verticalScrollBar().setValue(
            self.message_area.verticalScrollBar().maximum()
        ))

    def _clear_chat_display(self):
        """Leert die ScrollArea visuell ohne Daten zu verlieren."""
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

    def eventFilter(self, obj, event):
        # Enter sendet, Shift+Enter macht Zeilenumbruch
        if obj == self.message_text and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                self.send_message()
                return True
        return super().eventFilter(obj, event)


# ─────────────────────────────────────────────────────────────────────────────
#  Einstiegspunkt
# ─────────────────────────────────────────────────────────────────────────────
def main():
    INIT()
    get_server_info()

    if not servers:
        log.error("Keine Serverinformationen verfügbar. Bitte Server Mirror überprüfen.")
        sys.exit(1)

    if len(servers) == 1:
        server_info = servers[0]
        log.info(f"Einziger Server gefunden: {server_info}")
    else:
        log.info("Mehrere Server gefunden:")
        for idx, srv in enumerate(servers):
            log.info(f"{idx+1}. {srv}")
    
    # ensure the globals used by ServerConnection are updated
    global server_host, server_port, cert_port

    # Benutze den ersten Server in der Liste (kann später um Auswahl erweitert werden)
    server_host, _, _, server_port, cert_port = servers[0]

    log.info(f"Verwende Server: {server_host}:{server_port} (Zertifikat: Port {cert_port})")

    if GUI_ENABLED:
        app = QApplication(sys.argv)

        dialog = LoginSignupDialog()
        if dialog.exec_() != QDialog.Accepted:
            sys.exit(0)

        try:
            window = ChatWindow()
            window.show()
            sys.exit(app.exec_())
        except Exception as e:
            log.error(f"Fehler beim Öffnen des Chat-Fensters: {e}", exc_info=True)
            QMessageBox.critical(None, "Fehler", f"Fehler beim Öffnen des Chat-Fensters:\n{e}")
            sys.exit(1)
    else:
        conn = ServerConnection(server_host, server_port)
        log.info("Running in CLI mode.")
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
                log.info("Exiting.")
                conn.close()
                break
            else:
                log.warning("Unbekannter Befehl.")


if __name__ == "__main__":
    main()