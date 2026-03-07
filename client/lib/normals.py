import os

CERT_PATH = os.path.expanduser("~/.aspm_cert.pem")

server_host = "127.0.0.1"
server_port = 8080
cert_port = 8282

USERNAME = None
PASSWORD = None
USERID   = None

_servers = []
_cache = {}
