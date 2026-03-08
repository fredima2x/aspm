import os

CERT_PATH = os.path.expanduser("~/.aspm_cert.pem")

server_host = ""
server_port = 0
cert_port = 8282

MIRROR_SERVER_HOST = "192.168.178.138"
MIRROR_SERVER_PORT = 8282

USERNAME = None
PASSWORD = None
USERID   = None

_servers = []
_cache = {}
