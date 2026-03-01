from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, 
                              QVBoxLayout, QHBoxLayout, QSizePolicy,
                              QListWidgetItem, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5 import uic
import sys

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui/gui.ui", self)
        
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
        """Öffnet einen Dialog und legt einen neuen Chat an."""
        name, ok = QInputDialog.getText(self, "Neuer Chat", "Chat-Name:")
        if ok and name.strip():
            name = name.strip()
            if name in self.chats:
                QMessageBox.warning(self, "Fehler", f"Ein Chat namens '{name}' existiert bereits.")
            else:
                self._create_chat(name)

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
        """Wird aufgerufen wenn der Nutzer in der Sidebar einen anderen Chat anklickt."""
        if not current:
            return
        
        # Nachrichten des aktuellen Chats speichern bevor wir wechseln –
        # das passiert automatisch, weil wir sie in self.chats[name]["messages"] ablegen.
        
        self.current_chat = current.text()
        self._clear_chat_display()
        
        # Alle gespeicherten Nachrichten dieses Chats neu aufbauen
        for text, received in self.chats[self.current_chat]["messages"]:
            self._draw_bubble(text, received)

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
        """
        Fügt eine Nachricht hinzu und speichert sie in der Datenstruktur.
        Der optionale Parameter 'chat' erlaubt es, Nachrichten in einen
        bestimmten Chat zu schreiben, auch wenn er gerade nicht angezeigt wird.
        """
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


app = QApplication(sys.argv)
window = ChatWindow()
window.show()
sys.exit(app.exec_())