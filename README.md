# MCEFLI - Multi-Client Efficient File and Live Internet Messenger

A lightweight, Python-based client-server messenger application designed for real-time communication with persistent chat history and user management.

## 📋 Overview

MCEFLI is a command-line messenger that allows users to:
- Create accounts with secure password authentication
- Create and manage multiple chat groups
- Send and receive messages in real-time
- Manage chat members (add/remove users)
- View chat history and available chats

**Current Version:** 1.6.0

## 🏗️ Architecture

### Components

```
MCEFLI/
├── client/
│   └── client.py          # Client application with CLI interface
├── server/
│   ├── server.py          # Main server with socket handling
│   └── datasm.py          # SQLite database manager
├── dokumentation/         # API documentation
└── env/                   # Python virtual environment
```

### System Design

- **Client**: Command-line interface that connects to the server via TCP sockets
- **Server**: Multi-threaded server handling concurrent client connections
- **Database**: SQLite database for persistent storage of users, messages, and chats
- **Protocol**: Custom TCP protocol with semicolon-separated command format

## 🚀 Features

- ✅ User Authentication (Sign up / Sign in)
- ✅ Secure Password Storage (SHA256 hashing with salt)
- ✅ Multiple Chat Support
- ✅ Real-time Message Exchange
- ✅ Chat Member Management
- ✅ Message History
- ✅ Multi-threaded Server Architecture
- ✅ Thread-safe Database Operations

## 💻 Installation

### Prerequisites

- Python 3.x
- SQLite3 (included with Python)

### Setup

1. **Clone or navigate to the project:**
   ```bash
   cd /home/fredima2x/code/mcefli
   ```

2. **Activate the virtual environment:**
   ```bash
   source env/bin/activate
   ```

3. **Install dependencies (if needed):**
   The project uses only Python standard library. Core dependencies are already in the virtual environment.

## 🎯 Usage

### Starting the Server

```bash
python server/server.py
```

The server will listen on `localhost:8080` by default.

### Starting the Client

In a separate terminal:

```bash
python client/client.py
```

### Client Commands

Once connected, use the following commands:

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Display all available commands | `help` |
| `exit` | Disconnect from server | `exit` |
| `list_chats` | Show all your chats | `list_chats` |
| `new_chat <name>` | Create a new chat | `new_chat MyGroup` |
| `select_chat <id>` | Select a chat to work with | `select_chat 1` |
| `send_msg <message>` | Send a message to selected chat | `send_msg Hello!` |
| `view_messages` | View all messages in selected chat | `view_messages` |
| `add_user <id/username>` | Add a user to the chat | `add_user john` |
| `remove_user <id/username>` | Remove a user from the chat | `remove_user john` |

### Login/Signup Flow

1. Run the client
2. When prompted, choose to create a new account (`y`) or login with existing credentials (`n`)
3. Enter your username and password
4. You're now authenticated and can use all commands

## 🗄️ Database Schema

### Users Table
```sql
- user_id (INTEGER PRIMARY KEY)
- nickname (TEXT UNIQUE)
- password_hash (TEXT)
- salt (TEXT)
- properties (TEXT)
- created_at (TIMESTAMP)
```

### Messages Table
```sql
- message_id (INTEGER PRIMARY KEY)
- sender_id (INTEGER)
- chat_id (INTEGER)
- content (TEXT)
- properties (TEXT)
- send_at (TIMESTAMP)
```

### Chats Table
```sql
- chat_id (INTEGER PRIMARY KEY)
- creator_id (INTEGER)
- members (TEXT)
- properties (TEXT)
- created_at (TIMESTAMP)
```

## 🔐 Security

- **Password Storage**: Uses SHA256 hashing with 32-byte random salt
- **User Verification**: Server-side credential validation
- **Thread Safety**: Mutex locks for concurrent database access
- **Socket Security**: Encrypted credential transmission support ready

## ⚙️ Configuration

### Server Configuration

Edit `server/server.py`:
```python
SERVER_PORT = 8080          # Default server port
```

### Client Configuration

Edit `client/client.py`:
```python
SERVER_HOST = "localhost"   # Server address
SERVER_PORT = 8080          # Server port (must match server)
GUI_ENABLED = False         # CLI mode (GUI support in development)
```

## 📡 Protocol

Commands are transmitted using a semicolon-separated format:

**Format:** `<command>;<arg1>;<arg2>;...`

### Authentication Commands
- `send_creds;{username};{password}` - Login with existing account
- `send_newuser;{username};{password}` - Create new account

### Chat Commands
- `get_chats` - Retrieve all chats for user
- `new_chat;{name}` - Create new chat
- `get_messages;{chat_id}` - Get messages from chat

### Message Commands
- `send_message;{chat_id};{content}` - Send message to chat

## 🐛 Debugging

The server includes comprehensive logging:
- Logs are printed to console
- Default log level: DEBUG
- All client connections and commands are logged

To view server logs, check the terminal output where the server is running.

## 📝 Documentation

Additional documentation available in:
- `dokumentation/server_commands.md` - Detailed server command protocol
- `dokumentation/DatabaseManager_API_Dokumentation.md` - Database API reference

## 🛠️ Development Notes

- **GUI Support**: Framework ready but currently disabled (`GUI_ENABLED = False`)
- **Async Messaging**: Currently synchronous; async implementation available in development branch
- **Database**: SQLite for local deployment; scalable to PostgreSQL for production

## 📋 Requirements

- Python 3.x
- Standard Library: socket, threading, time, json, sqlite3, hashlib, logging

## 📄 License

[Add your license information here]

## 👥 Contributing

To contribute:
1. Create a feature branch
2. Test thoroughly on both server and client
3. Submit your changes with detailed descriptions

## ❓ FAQ

**Q: Can I use this on a network?**
A: Yes! Change `SERVER_HOST` in client configuration from "localhost" to the server's IP address.

**Q: How many users can connect simultaneously?**
A: Limited by Python's thread capacity and system resources. Tested with multiple concurrent clients.

**Q: Is the database file persistent?**
A: Yes, `messenger.db` is created in the working directory on first run and persists all data.

## 🔧 Troubleshooting

- **Connection Refused**: Ensure server is running and listening on the correct port
- **Authentication Failed**: Check username and password
- **Database Locked**: Ensure only one server instance is running
- **Socket Error**: Verify firewall settings if connecting remotely

---

**Happy Messaging! 💬**
