
VERSION = "1.12.1-8"
VERSION_SIMPLE = "1.12.1"
VERSIONS_COMPATIBILITY = {
    "1.12.1": ["1.12.1-8", "1.12.1-7", "1.12.1-6", "1.12.1-5", "1.12.1-4", "1.12.1-3", "1.12.1-2", "1.12.1-1"],
}

import os
import socket
import sys
import time
import json as js
import logging

import lib.CliInterface as CliInterface
import lib.LoginDialogue as LoginDialogue
import lib.MainWindow as MainWindow
import lib.normals as normals
import lib.Caching as Caching

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
MIRROR_SERVER_HOST = "localhost"
MIRROR_SERVER_PORT = 8282
GUI_ENABLED = True
normals._servers = []


# ─────────────────────────────────────────────────────────────────────────────
#  Logging
# ─────────────────────────────────────────────────────────────────────────────
def INIT():
    global log
    Caching.main()  # Starte den Caching-Thread
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    log = logging.getLogger(__name__)

def get_server_info():
    try:
        with socket.create_connection((MIRROR_SERVER_HOST, MIRROR_SERVER_PORT), timeout=5) as sock:
            data = sock.recv(4096).decode()
            normals._servers = js.loads(data)
            log.info(f"Empfangene Serverinformationen: {normals._servers}")
    except Exception as e:
        log.error(f"Fehler beim Abrufen der Serverinformationen: {e}")
    # "with" block handles socket closing automatically; no finally block needed
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  Einstiegspunkt
# ─────────────────────────────────────────────────────────────────────────────
def main():
    INIT()
    get_server_info()

    if not normals._servers:
        log.error("Keine Serverinformationen verfügbar. Bitte Server Mirror überprüfen.")
        sys.exit(1)

    if len(normals._servers) == 1:
        server_info = normals._servers[0]
        log.info(f"Einziger Server gefunden: {server_info}")
    else:
        log.info("Mehrere Server gefunden:")
        for idx, srv in enumerate(normals._servers):
            log.info(f"{idx+1}. {srv}")
    
    # ensure the globals used by ServerConnection are updated
    global server_host, server_port, cert_port

    # Benutze den ersten Server in der Liste (kann später um Auswahl erweitert werden)
    server_host, _, _, server_port, cert_port = normals._servers[0]

    log.info(f"Verwende Server: {server_host}:{server_port} (Zertifikat: Port {cert_port})")

    # Update global variables in normals module so other modules can use them
    normals.server_host = server_host
    normals.server_port = server_port
    normals.cert_port = cert_port

    if GUI_ENABLED:
        app = QApplication(sys.argv)

        dialog = LoginDialogue.LoginSignupDialog()
        if dialog.exec_() != QDialog.Accepted:
            sys.exit(0)

        try:
            window = MainWindow.ChatWindow()
            window.show()
            sys.exit(app.exec_())
        except Exception as e:
            log.error(f"Fehler beim Öffnen des Chat-Fensters: {e}", exc_info=True)
            QMessageBox.critical(None, "Fehler", f"Fehler beim Öffnen des Chat-Fensters:\n{e}")
            sys.exit(1)
    else:
        CliInterface.run_cli(server_host, server_port, cert_port)
        


if __name__ == "__main__":
    main()
