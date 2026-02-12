import datasm
db = datasm.DatabaseManager()
ID = db.verify_user("fredima2x", "1234")
if ID is None:
    ID = db.create_user("fredima2x", "1234")
    print(f"User erstellt mit ID: {ID}")
else:
    print(f"User gefunden mit ID: {ID}")
db.save_message(ID, 1, "Hello World!")
messages = db.load_messages(1)
print(f"Nachrichten: {messages}")
'''
User gefunden mit ID: 1
Nachrichten: [(1, 'Hello World!', None)]
'''