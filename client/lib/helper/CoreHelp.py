import sys
import os
import socket
import time
import json as js
import logging as log   

import client.lib.core.normals as normals


log.basicConfig(level=log.INFO)

def resource_path(relative_path):
    """Gibt den korrekten Pfad zurück – im Dev-Modus und nach PyInstaller-Build."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller-Build: Dateien sind in einem temp-Ordner entpackt
        base_path = sys._MEIPASS
    else:
        # Normaler Dev-Modus
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def fetch_certificate(host, port):
    if os.path.exists(normals.CERT_PATH):
        return
    print(f"Erstes Verbinden – lade Zertifikat von {host}:{port} ...")
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            cert_pem = sock.recv(8192).decode()
            with open(normals.CERT_PATH, "w") as f:
                f.write(cert_pem)
        print(f"Zertifikat gespeichert: {normals.CERT_PATH}")
    except Exception as e:
        log.error(f"Fehler beim Abrufen des Zertifikats: {e}")
        raise