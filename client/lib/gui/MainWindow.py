import logging
import time
import json as js
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QLabel,
    QVBoxLayout, QHBoxLayout, QSizePolicy,
    QListWidgetItem, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5 import uic

import lib.gui.SearchWindow as SearchWindow
import lib.core.ServerConnection as ServerConnection
import lib.core.normals as normals
from lib.helper.CoreHelp import resource_path
from lib.gui.SmoothScrollArea import SmoothScrollArea

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log = logging.getLogger(__name__)
        try:
            self.log.info("ChatWindow: Lade UI...")
            uic.loadUi(resource_path("assets/dep_gui.ui"), self)
            self.log.info("ChatWindow: UI geladen")
        except Exception as e:
            self.log.error(f"ChatWindow: Fehler beim Laden der UI: {e}", exc_info=True)
            raise

        try:
            self.log.info("ChatWindow: Verbinde zum Server...")
            self.conn = ServerConnection.ServerConnection(normals.server_host, normals.server_port, normals.cert_port)
            self.log.info("ChatWindow: Mit Server verbunden")
        except Exception as e:
            self.log.error(f"ChatWindow: Fehler beim Verbinden: {e}", exc_info=True)
            raise

        self.username = normals.USERNAME
        self.password = normals.PASSWORD
        self.user_id = normals.USERID

        # verify
        if not self.conn.status():
            self.log.error("ChatWindow: Verbindung zum Server fehlgeschlagen.")
            QMessageBox.critical(self, "Fehler", "Verbindung zum Server fehlgeschlagen.")
            sys.exit(1)

        time.sleep(0.5)  # Kurze Pause, damit die Verbindung stabil ist

        try:
            self.conn.verify_credentials(self.username, self.password)
            self.my_sender_id = self.conn.get_myuser_id()
            self.log.info(f"ChatWindow: Benutzer-ID ist {self.my_sender_id}")
        except Exception as e:
            self.log.error(f"ChatWindow: Fehler bei der Verifizierungsanfrage: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", "Fehler bei der Verifizierungsanfrage.")
            sys.exit(1)


        self.current_chat_id   = None
        self.last_message_id   = None

        try:
            self.log.info("ChatWindow: Richte ScrollArea ein...")
            self.chat_layout = QVBoxLayout(self.scrollAreaWidgetContents)
            self.chat_layout.setAlignment(Qt.AlignTop)
            self.chat_layout.setSpacing(8)
            self.chat_layout.setContentsMargins(10, 10, 10, 10)
            self.log.info("ChatWindow: ScrollArea eingerichtet")
        except Exception as e:
            self.log.error(f"ChatWindow: Fehler beim Einrichten der ScrollArea: {e}", exc_info=True)
            raise

        self.setWindowTitle(f"ASPM – {self.username}")

        try:
            self.log.info("ChatWindow: Verbinde Signale...")
            self.send_button.clicked.connect(self.send_message)
            self.message_text.installEventFilter(self)
            self.addchat_button.clicked.connect(self.add_chat)
            self.rmchat_button.clicked.connect(self.remove_chat)
            self.adduser_button.clicked.connect(self.add_user)
            self.rmuser_button.clicked.connect(self.remove_user)
            self.listWidget.currentItemChanged.connect(self.switch_chat)
            self.log.info("ChatWindow: Signale verbunden")
        except Exception as e:
            self.log.error(f"ChatWindow: Fehler beim Verbinden der Signale: {e}", exc_info=True)
            raise

        try:
            self.log.info("ChatWindow: Lade Chatliste...")
            self.load_chat_list(initial=True)
            self.log.info("ChatWindow: Chatliste geladen")
        except Exception as e:
            self.log.error(f"ChatWindow: Fehler beim Laden der Chatliste: {e}", exc_info=True)
            raise

        try:
            self.log.info("ChatWindow: Starte Timer...")
            self.msg_timer = QTimer(self)
            self.msg_timer.setInterval(3000)
            self.msg_timer.timeout.connect(self._poll_messages)
            self.msg_timer.start()

            self.conn_timer = QTimer(self)
            self.conn_timer.setInterval(1000)
            self.conn_timer.timeout.connect(self._check_connection)
            self.conn_timer.start()

            self.chat_timer = QTimer(self)
            self.chat_timer.setInterval(15000)
            self.chat_timer.timeout.connect(self.load_chat_list)
            self.chat_timer.start()

            self.log.info("ChatWindow: Timer gestartet")
        except Exception as e:
            self.log.error(f"ChatWindow: Fehler beim Starten der Timer: {e}", exc_info=True)
            raise

        self.log.info("ChatWindow: Initialisierung abgeschlossen")

    # ── Chatliste ──────────────────────────────────────────────────────────

    def load_chat_list(self, initial=False):
        """Lädt alle Chats vom Server und füllt die Sidebar."""
        chats = self.conn.group_list()
        if chats is None:
            QMessageBox.warning(self, "Fehler", "Chatliste konnte nicht geladen werden.")
            return

        previously_selected_id = self.current_chat_id

        self.listWidget.blockSignals(True)
        self.listWidget.clear()

        for chat in chats:
            chat_id      = chat["chat_id"]
            members      = chat.get("members", [])
            member_count = len(members)

            # Member-Liste am Item speichern (UserRole+1)
            item = QListWidgetItem(f"Chat #{chat_id}  ({member_count} Mitglieder)")
            item.setData(Qt.UserRole,     chat_id)
            item.setData(Qt.UserRole + 1, members)   # ← Member-IDs mitspeichern
            self.listWidget.addItem(item)

            if chat_id == previously_selected_id:
                self.listWidget.setCurrentItem(item)

        self.listWidget.blockSignals(False)

        if self.listWidget.currentItem() is None and self.listWidget.count() > 0:
            self.listWidget.setCurrentRow(0)

        # Rechte Liste für aktuell gewählten Chat befüllen
        current = self.listWidget.currentItem()
        if current:
            self._populate_user_list(current.data(Qt.UserRole + 1))


    def _populate_user_list(self, member_ids: list):
        """Zeigt alle User des aktuellen Chats in der rechten ScrollArea."""
        # Layout einmalig anlegen
        if not hasattr(self, '_user_list_layout'):
            self._user_list_layout = QVBoxLayout()
            self._user_list_layout.setAlignment(Qt.AlignTop)
            self.scrollAreaWidgetContents_2.setLayout(self._user_list_layout)

        # Alte Einträge leeren
        while self._user_list_layout.count():
            item = self._user_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for user_id in member_ids:
            try:
                info = self.conn.get_user_info(user_id)    # {"user_id":..., "nickname":...}
                nickname = info.get("nickname", f"User #{user_id}") if info else f"User #{user_id}"
            except Exception:
                nickname = f"User #{user_id}"

            label = QLabel(f"👤  {nickname}")
            label.setStyleSheet("padding: 4px 8px;")
            self._user_list_layout.addWidget(label)


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


        if not is_own:
            if not f"user_info_{sender_id}" in normals._cache:
                json_user_info = self.conn.get_user_info(sender_id)
                user_info = json_user_info if isinstance(json_user_info, dict) else (js.loads(json_user_info) if json_user_info else {})
                normals._cache[f"user_info_{sender_id}"] = user_info
            else:
                user_info = normals._cache[f"user_info_{sender_id}"]
            sender_name = user_info.get("nickname", f"User #{sender_id}")


        if is_own:
            self._draw_bubble(content, received=False, timestamp=timestamp)
        else:
            self._draw_bubble(f"{sender_name}: {content}", received=True, timestamp=timestamp)

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
        
        dialog = SearchWindow.SearchWindow(self.conn)
        if dialog.exec_() == QDialog.Accepted:
            ok = True
            userdata = dialog.selected_user
            username = userdata["nickname"]
        else:
            return

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

    def _check_connection(self):
        """Überprüft die Verbindung zum Server. Bei Verbindungsfehlern wird der Benutzer informiert."""
        self.log.debug("Überprüfe Serververbindung...")
        if not self.conn.status():
            self.log.warning("Verbindung zum Server verloren.")
            QMessageBox.critical(self, "Verbindungsfehler", "Die Verbindung zum Server wurde unterbrochen.")
            time.sleep(1)  # Kurze Pause, damit der Benutzer die Nachricht sieht
            QMessageBox.information(self, "Reconnect", "Versuche, die Verbindung wiederherzustellen...")
            self.conn.close()
            while not self.conn.status():
                try:
                    self.conn = ServerConnection.ServerConnection(normals.server_host, normals.server_port, normals.cert_port)
                    if not self.conn.status():
                        # Ask if user wants to retry
                        retry = QMessageBox.question(
                            self, "Reconnect fehlgeschlagen",
                            "Verbindung konnte nicht wiederhergestellt werden. Nochmal versuchen?",
                            QMessageBox.Yes | QMessageBox.No
                        )                    
                        if not retry == QMessageBox.Yes:
                            sys.exit(1)
                except Exception as e:
                    self.log.error(f"Fehler beim erneuten Verbinden: {e}")
            try:
                self.conn.verify_credentials(self.username, self.password)
            except Exception as e:
                self.log.error(f"Fehler bei Verifizierungsanfrage nach Reconnect: {e}")
                QMessageBox.critical(self, "Fehler", "Fehler bei Verifizierungsanfrage nach Reconnect.")
                sys.exit(1)
        self.log.debug("Serververbindung ist stabil.")
        
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
