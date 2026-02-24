# DatabaseManager API Dokumentation

## User-Verwaltung

### `create_user(nickname, password)`
Erstellt einen neuen Benutzer mit sicherer Passwort-Speicherung (SHA-256 + Salt).

**Parameter:**
- `nickname` (str): Eindeutiger Benutzername
- `password` (str): Passwort im Klartext

**Rückgabe:**
- `int`: User-ID bei Erfolg
- `None`: Bei Fehler (Username bereits vergeben)

**Beispiel:**
```python
user_id = db.create_user("alice", "password123")
if user_id:
    print(f"User erstellt: ID {user_id}")
else:
    print("Username bereits vergeben")
```

---

### `verify_user(username, password)`
Überprüft Login-Credentials.

**Parameter:**
- `username` (str): Benutzername
- `password` (str): Passwort

**Rückgabe:**
- `int`: User-ID bei erfolgreicher Authentifizierung
- `None`: Bei falschen Credentials

**Beispiel:**
```python
user_id = db.verify_user("alice", "password123")
if user_id:
    print("Login erfolgreich")
else:
    print("Falscher Benutzername oder Passwort")
```

---

### `get_user_by_id(user_id)`
Ruft Benutzer-Informationen anhand der ID ab.

**Parameter:**
- `user_id` (int): Die User-ID

**Rückgabe:**
```python
{
    'user_id': 1,
    'nickname': 'alice',
    'properties': None,  # JSON-String oder None
    'created_at': '2025-02-14 10:30:00'
}
```
- `None`: User existiert nicht

**Beispiel:**
```python
user = db.get_user_by_id(1)
if user:
    print(f"Nickname: {user['nickname']}")
```

---

### `get_user_by_nickname(nickname)`
Sucht Benutzer nach Nickname.

**Parameter:**
- `nickname` (str): Der Benutzername

**Rückgabe:**
```python
{
    'user_id': 1,
    'nickname': 'alice',
    'properties': None
}
```
- `None`: User existiert nicht

**Beispiel:**
```python
user = db.get_user_by_nickname("alice")
if user:
    print(f"User-ID: {user['user_id']}")
```

---

### `search_users(query)`
Sucht Benutzer mit SQL LIKE-Matching (findet Teilstrings).

**Parameter:**
- `query` (str): Suchbegriff

**Rückgabe:**
```python
[
    {'user_id': 1, 'nickname': 'alice'},
    {'user_id': 5, 'nickname': 'alicia'},
    {'user_id': 8, 'nickname': 'malik'}
]
```

**Beispiel:**
```python
results = db.search_users("ali")
# Findet: alice, alicia, malik, etc.
for user in results:
    print(f"{user['user_id']}: {user['nickname']}")
```

---

## Chat-Verwaltung

### `new_chat(creator_id, properties=None)`
Erstellt einen neuen Chat.

**Parameter:**
- `creator_id` (int): User-ID des Erstellers
- `properties` (str, optional): JSON-String mit Chat-Metadaten

**Rückgabe:**
- `int`: Chat-ID bei Erfolg
- `None`: Bei Fehler

**Beispiel:**
```python
chat_id = db.new_chat(
    creator_id=1,
    properties='{"name": "Team Meeting", "avatar": "🚀"}'
)
print(f"Chat erstellt: ID {chat_id}")
```

---

### `add_to_chat(chat_id, user_id)`
Fügt einen Benutzer zum Chat hinzu.

**Parameter:**
- `chat_id` (int): Die Chat-ID
- `user_id` (int): Die User-ID

**Rückgabe:**
- `True`: Erfolgreich hinzugefügt
- `False`: Fehler (Chat existiert nicht, User bereits Mitglied)

**Beispiel:**
```python
success = db.add_to_chat(chat_id=5, user_id=2)
if success:
    print("User zum Chat hinzugefügt")
else:
    print("Fehler beim Hinzufügen")
```

---

### `remove_from_chat(chat_id, user_id)`
Entfernt einen Benutzer aus dem Chat.

**Parameter:**
- `chat_id` (int): Die Chat-ID
- `user_id` (int): Die User-ID

**Rückgabe:**
- `True`: Erfolgreich entfernt
- `False`: Fehler (Chat existiert nicht, User nicht Mitglied)

**Beispiel:**
```python
removed = db.remove_from_chat(chat_id=5, user_id=2)
if removed:
    print("User aus Chat entfernt")
```

---

### `get_chat_members(chat_id)`
Gibt alle Mitglieder eines Chats zurück (inkl. Creator).

**Parameter:**
- `chat_id` (int): Die Chat-ID

**Rückgabe:**
- `list[int]`: Liste von User-IDs
- `None`: Chat existiert nicht

**Beispiel:**
```python
members = db.get_chat_members(5)
if members:
    print(f"Mitglieder: {members}")  # [1, 2, 3, 7]
else:
    print("Chat existiert nicht")
```

---

### `get_user_chats(user_id)`
Ruft alle Chats eines Benutzers ab (sowohl als Mitglied als auch als Creator).

**Parameter:**
- `user_id` (int): Die User-ID

**Rückgabe:**
```python
[
    {
        'chat_id': 1,
        'creator_id': 5,
        'members': [1, 2, 5],
        'properties': '{"name": "Team Chat"}',
        'created_at': '2025-02-14 10:00:00'
    },
    {
        'chat_id': 3,
        'creator_id': 1,
        'members': [1, 8],
        'properties': None,
        'created_at': '2025-02-14 11:30:00'
    }
]
```

**Beispiel:**
```python
chats = db.get_user_chats(user_id=1)
for chat in chats:
    member_count = len(chat['members'])
    print(f"Chat {chat['chat_id']}: {member_count} Mitglieder")
```

---

### `delete_chat(chat_id)`
Löscht einen Chat aus der Datenbank.

**⚠️ Warnung:** Nachrichten bleiben in der Datenbank erhalten (kein CASCADE).

**Parameter:**
- `chat_id` (int): Die Chat-ID

**Rückgabe:**
- `True`: Erfolgreich gelöscht
- `False`: Fehler

**Beispiel:**
```python
deleted = db.delete_chat(5)
if deleted:
    print("Chat gelöscht")
```

---

## Nachrichten-Verwaltung

### `save_message(sender_id, chat_id, content, properties=None)`
Speichert eine neue Nachricht in der Datenbank.

**Parameter:**
- `sender_id` (int): User-ID des Absenders
- `chat_id` (int): Ziel-Chat-ID
- `content` (str): Nachrichtentext
- `properties` (str, optional): JSON-String für Metadaten

**Rückgabe:**
- `None` (Fehler werden nur geloggt, nicht zurückgegeben)

**Beispiel:**
```python
db.save_message(
    sender_id=1,
    chat_id=5,
    content="Hallo Welt!",
    properties='{"type": "text", "mentions": [2, 3]}'
)
```

**Properties-Beispiele:**
```python
# Text-Nachricht mit Mentions
properties='{"type": "text", "mentions": [2, 3]}'

# Bild-Nachricht
properties='{"type": "image", "url": "/uploads/img123.jpg", "width": 800}'

# System-Nachricht
properties='{"type": "system", "event": "user_joined"}'
```

---

### `get_messages(chat_id, limit=50, offset=0)`
Ruft Nachrichten mit Pagination ab.

**Sortierung:** Neueste zuerst (ORDER BY send_at DESC)

**Parameter:**
- `chat_id` (int): Die Chat-ID
- `limit` (int, default=50): Maximale Anzahl Nachrichten
- `offset` (int, default=0): Offset für Pagination

**Rückgabe:**
```python
[
    {
        'message_id': 42,
        'sender_id': 1,
        'content': 'Hallo!',
        'properties': '{"type": "text"}',
        'send_at': '2025-02-14 15:30:00'
    },
    {
        'message_id': 41,
        'sender_id': 2,
        'content': 'Hi zurück!',
        'properties': None,
        'send_at': '2025-02-14 15:29:55'
    }
]
```

**Beispiel:**
```python
# Erste 20 Nachrichten laden
messages = db.get_messages(chat_id=5, limit=20)
for msg in messages:
    print(f"User {msg['sender_id']}: {msg['content']}")

# Pagination: Seite 2 (Nachrichten 21-40)
older_messages = db.get_messages(chat_id=5, limit=20, offset=20)

# Alle Nachrichten laden (Vorsicht bei großen Chats!)
all_messages = db.get_messages(chat_id=5, limit=999999)
```

---

### `load_messages(chat_id)` ⚠️ Legacy
**Veraltet!** Nutze stattdessen `get_messages()`.

Gibt Nachrichten **ohne** `message_id` und `send_at` zurück.

**Parameter:**
- `chat_id` (int): Die Chat-ID

**Rückgabe:**
```python
[
    (sender_id, content, properties),
    (1, 'Hallo', None),
    (2, 'Hi', '{"type": "text"}')
]
```

**Beispiel:**
```python
messages = db.load_messages(5)
for sender_id, content, properties in messages:
    print(f"User {sender_id}: {content}")
```

---

### `delete_message(message_id, user_id)`
Löscht eine Nachricht. **Wichtig:** Nur der Absender kann seine eigene Nachricht löschen.

**Parameter:**
- `message_id` (int): Die Nachrichten-ID
- `user_id` (int): User-ID (muss Absender sein)

**Rückgabe:**
- `True`: Erfolgreich gelöscht
- `False`: Keine Berechtigung oder Nachricht existiert nicht

**Beispiel:**
```python
deleted = db.delete_message(message_id=42, user_id=1)
if deleted:
    print("Nachricht gelöscht")
else:
    print("Keine Berechtigung oder Nachricht nicht gefunden")
```

---

## Vollständiges Workflow-Beispiel

```python
from datasm import DatabaseManager

# Datenbank initialisieren
db = DatabaseManager()

# 1. User registrieren
alice_id = db.create_user("alice", "password123")
bob_id = db.create_user("bob", "securepass")
charlie_id = db.create_user("charlie", "mypassword")

# 2. Login
user_id = db.verify_user("alice", "password123")
if user_id:
    print(f"Alice eingeloggt (ID: {user_id})")

# 3. Chat erstellen
chat_id = db.new_chat(
    creator_id=alice_id,
    properties='{"name": "Projekt Alpha", "type": "group"}'
)
print(f"Chat erstellt: {chat_id}")

# 4. Mitglieder hinzufügen
db.add_to_chat(chat_id, bob_id)
db.add_to_chat(chat_id, charlie_id)

# 5. Mitglieder anzeigen
members = db.get_chat_members(chat_id)
print(f"Mitglieder: {members}")  # [1, 2, 3]

# 6. Nachrichten senden
db.save_message(alice_id, chat_id, "Hallo Team!", '{"type": "text"}')
db.save_message(bob_id, chat_id, "Hi Alice!", '{"type": "text"}')
db.save_message(charlie_id, chat_id, "Hey zusammen!", '{"type": "text"}')

# 7. Nachrichten abrufen
messages = db.get_messages(chat_id, limit=10)
for msg in messages:
    user = db.get_user_by_id(msg['sender_id'])
    print(f"{user['nickname']}: {msg['content']}")

# 8. Alle Chats von Alice
chats = db.get_user_chats(alice_id)
print(f"Alice ist in {len(chats)} Chat(s)")

# 9. User suchen
results = db.search_users("bob")
for user in results:
    print(f"Gefunden: {user['nickname']}")

# 10. Nachricht löschen
first_msg_id = messages[-1]['message_id']  # Älteste Nachricht
db.delete_message(first_msg_id, alice_id)

# 11. User aus Chat entfernen
db.remove_from_chat(chat_id, charlie_id)

# 12. Chat löschen
db.delete_chat(chat_id)
```

---

## Properties (JSON-String Format)

Properties sind flexible JSON-Strings für zusätzliche Metadaten.

### User Properties
```python
properties='{"avatar": "👤", "status": "online", "bio": "Developer"}'
```

### Chat Properties
```python
properties='{"name": "Team Meeting", "avatar": "🚀", "type": "group", "muted": false}'
```

### Message Properties
```python
# Text-Nachricht
properties='{"type": "text"}'

# Nachricht mit Mentions
properties='{"type": "text", "mentions": [2, 3, 5]}'

# Bild-Nachricht
properties='{"type": "image", "url": "/uploads/img.jpg", "width": 1920, "height": 1080}'

# System-Nachricht
properties='{"type": "system", "event": "user_joined", "user_id": 5}'

# Antwort auf Nachricht
properties='{"type": "text", "reply_to": 42}'
```

---

## Datenbank-Schema

### Tabelle: `users`
| Spalte        | Typ       | Beschreibung                     |
|---------------|-----------|----------------------------------|
| user_id       | INTEGER   | Primary Key (Auto-Increment)     |
| nickname      | TEXT      | Unique, Benutzername             |
| password_hash | TEXT      | SHA-256 Hash                     |
| salt          | TEXT      | 32-Zeichen Hex-String            |
| properties    | TEXT      | JSON-String (optional)           |
| created_at    | TIMESTAMP | Automatischer Zeitstempel        |

### Tabelle: `messages`
| Spalte      | Typ       | Beschreibung                     |
|-------------|-----------|----------------------------------|
| message_id  | INTEGER   | Primary Key (Auto-Increment)     |
| sender_id   | INTEGER   | Foreign Key → users.user_id      |
| chat_id     | INTEGER   | Foreign Key → chats.chat_id      |
| content     | TEXT      | Nachrichteninhalt                |
| properties  | TEXT      | JSON-String (optional)           |
| send_at     | TIMESTAMP | Automatischer Zeitstempel        |

### Tabelle: `chats`
| Spalte     | Typ       | Beschreibung                     |
|------------|-----------|----------------------------------|
| chat_id    | INTEGER   | Primary Key (Auto-Increment)     |
| creator_id | INTEGER   | Foreign Key → users.user_id      |
| members    | TEXT      | JSON-Array mit User-IDs          |
| properties | TEXT      | JSON-String (optional)           |
| created_at | TIMESTAMP | Automatischer Zeitstempel        |

---

## Sicherheitshinweise

### Passwort-Hashing
- SHA-256 mit zufälligem 32-Zeichen Salt
- Salt wird pro User generiert
- Passwörter werden **nie** im Klartext gespeichert

### SQL-Injection-Schutz
- Alle Queries verwenden Parameterized Statements (`?`)
- **Niemals** String-Concatenation für SQL verwenden

### Best Practices
- Validiere Input vor `create_user()` (min. Länge, erlaubte Zeichen)
- Prüfe Berechtigungen vor `delete_message()` und `remove_from_chat()`
- Verwende `get_chat_members()` um zu prüfen ob User Chat-Zugriff hat
- Logge sicherheitsrelevante Events (fehlgeschlagene Logins, etc.)

---

## Fehlerbehandlung

Alle Methoden haben integriertes Logging:

```python
import logging

# Logger-Level anpassen
logging.basicConfig(level=logging.DEBUG)  # Zeigt alle Debug-Meldungen
logging.basicConfig(level=logging.INFO)   # Standard
logging.basicConfig(level=logging.ERROR)  # Nur Fehler
```

**Geloggte Events:**
- `INFO`: Erfolgreiche Operationen (User created, Message saved)
- `WARNING`: Nicht-kritische Probleme (User bereits im Chat)
- `ERROR`: Fehler (Chat existiert nicht, DB-Fehler)
- `CRITICAL`: Schwere Fehler (Nachricht konnte nicht gespeichert werden)

---

## Tipps & Tricks

### 1. Pagination effizient nutzen
```python
# Lade Nachrichten in Batches von 50
offset = 0
while True:
    messages = db.get_messages(chat_id, limit=50, offset=offset)
    if not messages:
        break
    process_messages(messages)
    offset += 50
```

### 2. Chat-Namen aus Properties extrahieren
```python
import json

chat = db.get_user_chats(user_id)[0]
if chat['properties']:
    props = json.loads(chat['properties'])
    chat_name = props.get('name', f"Chat {chat['chat_id']}")
```

### 3. Ungelesene Nachrichten zählen
```python
# Speichere last_read_message_id in User-Properties
user = db.get_user_by_id(user_id)
props = json.loads(user['properties']) if user['properties'] else {}
last_read = props.get('last_read_message_id', 0)

messages = db.get_messages(chat_id)
unread = [m for m in messages if m['message_id'] > last_read]
print(f"{len(unread)} ungelesene Nachrichten")
```

### 4. Bulk-Operations vermeiden
```python
# ❌ Schlecht: N+1 Query Problem
for user_id in user_ids:
    db.add_to_chat(chat_id, user_id)  # N DB-Calls

# ✅ Besser: Füge users direkt zur members-Liste hinzu
# (Erfordert direkten DB-Zugriff, nicht in aktueller API)
```

---

**Version:** 1.0  
**Letzte Aktualisierung:** Februar 2025  
**Lizenz:** Siehe Projektlizenz
