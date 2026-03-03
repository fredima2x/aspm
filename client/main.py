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

# ─────────────────────────────────────────────────────────────────────────────
#  Konfiguration
# ─────────────────────────────────────────────────────────────────────────────
SERVER_HOST = "fredima.de"
SERVER_PORT = 8280
CERT_PORT   = 8281
CERT_PATH   = os.path.expanduser("~/.aspm_cert.pem")
GUI_ENABLED = True


# ─────────────────────────────────────────────────────────────────────────────
#  Logging
# ─────────────────────────────────────────────────────────────────────────────
def INIT():
    global log
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    log = logging.getLogger(__name__)


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
def fetch_certificate(host, port=CERT_PORT):
    if os.path.exists(CERT_PATH):
        return
    print(f"Erstes Verbinden – lade Zertifikat von {host}:{port} ...")
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port)) as raw_sock:
        with context.wrap_socket(raw_sock, server_hostname=host) as ssock:
            cert_der = ssock.getpeercert(binary_form=True)
            cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
            fingerprint = hashlib.sha256(cert_der).hexdigest()
            fp_fmt = ":".join(
                fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2)
            )
            with open(CERT_PATH, "w") as f:
                f.write(cert_pem)
    print(f"Zertifikat gespeichert: {CERT_PATH}")
    print(f"WICHTIG – Fingerprint beim Server prüfen: SHA-256: {fp_fmt}")


# ─────────────────────────────────────────────────────────────────────────────
#  Server-API
# ─────────────────────────────────────────────────────────────────────────────
class ServerConnection:
    def __init__(self, host, port):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.socket = None
        self.connect()

    def connect(self):
        try:
            fetch_certificate(self.host, CERT_PORT)
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
            raise
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise

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
    def __init__(self, conn):
        super().__init__()
        uic.loadUi(resource_path("assets/gui_login.ui"), self)
        self.conn = conn
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
        username = self.enter_username_line_2.text().strip()
        password = self.enter_password_line_2.text()

        if not username or not password:
            QMessageBox.warning(self, "Fehler", "Bitte Benutzername und Passwort eingeben.")
            return

        response = self.conn.verify_credentials(username, password, sign_up=False)
        if response == "verified":
            self.username = username
            self.accept()
        else:
            QMessageBox.warning(self, "Login fehlgeschlagen",
                                f"Ungültige Anmeldedaten.\nServer: {response}")
            self.enter_password_line_2.clear()
            self.enter_password_line_2.setFocus()

    def try_signup(self):
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
            self.username = username
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
    def __init__(self, conn, username):
        super().__init__()
        uic.loadUi(resource_path("assets/gui.ui"), self)

        self.conn     = conn
        self.username = username
        self.my_sender_id = self.conn.get_myuser_id()  # Eigene user_id für Nachrichtenvergleich

        self.current_chat_id   = None  # chat_id des aktiven Chats
        self.last_message_id   = None  # Höchste bekannte message_id – für Polling

        # ── ScrollArea vorbereiten ──────────────────────────────────────────
        self.chat_layout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(8)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)

        # ── Fenstertitel ───────────────────────────────────────────────────
        self.setWindowTitle(f"ASPM – {self.username}")

        # ── Signale verbinden ──────────────────────────────────────────────
        self.send_button.clicked.connect(self.send_message)
        self.message_text.installEventFilter(self)
        self.addchat_button.clicked.connect(self.add_chat)
        self.rmchat_button.clicked.connect(self.remove_chat)
        self.adduser_button.clicked.connect(self.add_user)
        self.rmuser_button.clicked.connect(self.remove_user)
        self.listWidget.currentItemChanged.connect(self.switch_chat)

        # ── Chatliste laden ────────────────────────────────────────────────
        self.load_chat_list()

        # ── Auto-Refresh Timer ─────────────────────────────────────────────
        # Nachrichten alle 3 Sekunden auf neue prüfen
        self.msg_timer = QTimer(self)
        self.msg_timer.setInterval(3000)
        self.msg_timer.timeout.connect(self._poll_messages)
        self.msg_timer.start()

        # Chatliste alle 30 Sekunden aktualisieren (neue Chats, Mitgliederzahl)
        self.chat_timer = QTimer(self)
        self.chat_timer.setInterval(30000)
        self.chat_timer.timeout.connect(self.load_chat_list)
        self.chat_timer.start()

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
        self.load_messages()

    # ── Nachrichten ────────────────────────────────────────────────────────

    def load_messages(self):
        """Lädt alle Nachrichten des aktuellen Chats und zeichnet sie (beim Chat-Wechsel)."""
        if not self.current_chat_id:
            return
        messages = self.conn.message_getall(self.current_chat_id)
        if messages is None:
            QMessageBox.warning(self, "Fehler", "Nachrichten konnten nicht geladen werden.")
            return

        self.last_message_id = None

        # Server gibt neueste Nachricht zuerst → umdrehen für chronologische Anzeige
        for msg in reversed(messages):
            self._render_message(msg)

        # Höchste ID merken für späteres Polling
        if messages:
            self.last_message_id = messages[0]["message_id"]  # Index 0 = neueste

    def _poll_messages(self):
        """
        Wird alle 3 Sekunden vom Timer aufgerufen.
        Holt nur neue Nachrichten (nach last_message_id) und hängt sie an.
        Kein komplettes Neuzeichnen – flackerfrei.
        """
        if not self.current_chat_id:
            return
        messages = self.conn.message_getall(self.current_chat_id)
        if not messages:
            return

        newest_id = messages[0]["message_id"]

        # Keine neuen Nachrichten → nichts tun
        if self.last_message_id is not None and newest_id <= self.last_message_id:
            return

        # Nur Nachrichten zeichnen die neuer sind als die letzte bekannte
        new_messages = [
            msg for msg in messages
            if self.last_message_id is None or msg["message_id"] > self.last_message_id
        ]

        # Chronologische Reihenfolge (älteste zuerst)
        for msg in reversed(new_messages):
            self._render_message(msg)

        self.last_message_id = newest_id

    def _render_message(self, msg):
        """Zeichnet eine einzelne Nachricht vom Server als Bubble."""
        sender_id = msg["sender_id"]
        content   = msg["content"]
        timestamp = msg.get("send_at", "")
        is_own    = (self.my_sender_id is not None and sender_id == self.my_sender_id)

        if is_own:
            self._draw_bubble(content, received=False, timestamp=timestamp)
        else:
            self._draw_bubble(f"User #{sender_id}: {content}", received=True, timestamp=timestamp)

    def send_message(self):
        text = self.message_text.toPlainText().strip()
        if not text:
            return
        if not self.current_chat_id:
            QMessageBox.warning(self, "Kein Chat", "Bitte zuerst einen Chat auswählen.")
            return

        response = self.conn.message_new(self.current_chat_id, text)
        if response == "message_saved":
            self.message_text.clear()
            self._poll_messages()
        else:
            QMessageBox.warning(self, "Fehler", f"Nachricht nicht gesendet.\nServer: {response}")

    # ── Teilnehmer-Verwaltung ──────────────────────────────────────────────

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
            time_part = timestamp.split(" ")[-1][:5] if " " in timestamp else timestamp[:5]
            display_text = f"{text}\n{time_part}"

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
    conn = ServerConnection(SERVER_HOST, SERVER_PORT)

    if GUI_ENABLED:
        app = QApplication(sys.argv)

        dialog = LoginSignupDialog(conn)
        if dialog.exec_() != QDialog.Accepted:
            sys.exit(0)

        window = ChatWindow(conn=conn, username=dialog.username)
        window.show()
        sys.exit(app.exec_())
    else:
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
                break
            else:
                log.warning("Unbekannter Befehl.")


if __name__ == "__main__":
    main()