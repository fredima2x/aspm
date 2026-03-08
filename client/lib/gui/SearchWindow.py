import logging
import time
import json as js
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QLabel,
    QVBoxLayout, QHBoxLayout, QSizePolicy,
    QListWidgetItem, QInputDialog, QMessageBox, QButtonGroup,
    QPushButton
)
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5 import uic

import lib.core.normals as normals
import lib.helper.CoreHelp as CoreHelp

class SearchWindow(QDialog):
    def __init__(self, connection):
        super().__init__()
        uic.loadUi(CoreHelp.resource_path("assets/search_user.ui"), self)
        self.conn = connection
        self.selected_user = None
        self.enter_button.clicked.connect(self._try_select)
        self.cancel_button.clicked.connect(self._try_cancel)

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scrollAreaWidgetContents.setLayout(self.scroll_layout)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.placeholder_label = QLabel("🔍 Suchbegriff eingeben...")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: gray; padding: 20px;")
        self.scroll_layout.addWidget(self.placeholder_label)

        # Suche mit kurzem Delay (vermeidet DB-Query bei jedem Tastendruck)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)  # 300ms nach letztem Tastendruck
        self.search_timer.timeout.connect(self._do_search)

        self.search_line.textChanged.connect(self._on_search_changed)

    def _on_search_changed(self, text: str):
        if not text.strip():
            self.search_timer.stop()
            self._clear_list()
            self.scroll_layout.addWidget(self.placeholder_label)  # ← wieder einfügen
            self.placeholder_label.show()
            return
        self.placeholder_label.hide()  # ← verstecken statt löschen
        self.search_timer.start() 

    def _do_search(self):
        """Wird 300ms nach dem letzten Tastendruck aufgerufen."""
        query = self.search_line.text().strip()
        if not query:
            return

        try:
            users = self.conn.search_users(query)  # DB-Abfrage
        except Exception as e:
            logging.error("Fehler bei User-Suche: %s", e)
            users = []

        self._populate(users)

    def _populate(self, users: list[dict]):
        self._clear_list()

        if not users:
            no_result = QLabel("Keine User gefunden.")
            no_result.setAlignment(Qt.AlignCenter)
            no_result.setStyleSheet("color: gray; padding: 20px;")
            self.scroll_layout.addWidget(no_result)
            return

        for user in users:
            btn = QPushButton(user["nickname"])
            btn.setCheckable(True)
            btn.setProperty("user_data", user)
            btn.setStyleSheet("""
                QPushButton           { text-align: left; padding: 6px 10px; border: 1px solid #ccc; border-radius: 4px; }
                QPushButton:checked   { background-color: #0078d4; color: white; border-color: #0078d4; }
                QPushButton:hover     { background-color: #e5f1fb; }
                QPushButton:checked:hover { background-color: #006cbf; }
            """)
            self.button_group.addButton(btn)
            self.scroll_layout.addWidget(btn)

    def _clear_list(self):
        for btn in self.button_group.buttons():
            self.button_group.removeButton(btn)
            btn.deleteLater()

        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget and widget is not self.placeholder_label:  # ← placeholder schützen
                widget.deleteLater()

    def _try_select(self):
        checked = self.button_group.checkedButton()
        if checked is None:
            self.main_label.setText("⚠️  Bitte erst einen User auswählen.")
            return
        self.selected_user = checked.property("user_data")
        self.accept()

    def _try_cancel(self):
        self.selected_user = None
        self.reject()

