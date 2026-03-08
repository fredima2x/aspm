from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QLabel,
    QVBoxLayout, QHBoxLayout, QSizePolicy,
    QListWidgetItem, QInputDialog, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5 import uic

import lib.core.ServerConnection as ServerConnection
import lib.helper.CoreHelp as CoreHelp
import lib.core.normals as normals

class LoginSignupDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(CoreHelp.resource_path("assets/dep_login.ui"), self)
        self.conn = ServerConnection.ServerConnection(normals.server_host, normals.server_port, normals.cert_port)
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
            normals.USERNAME = username
            normals.PASSWORD = password
            normals.USERID = self.conn.get_myuser_id()
            self.username = username
            self.conn.close()
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
            normals.USERNAME = username
            normals.PASSWORD = password
            normals.USERID = self.conn.get_myuser_id()
            self.username = username
            self.conn.close()  # Neue Verbindung im ChatWindow mit gültigen Credentials
            self.accept()
        else:
            QMessageBox.warning(self, "Registrierung fehlgeschlagen", f"Server: {response}")
            self.enter_password_line.clear()
            self.repeat_password_line.clear()
            self.enter_password_line.setFocus()