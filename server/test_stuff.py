import datasm

db = datasm.DatabaseManager()

ID = db.verify_user("fredima2x", "1234")
db.add_to_chat(1, ID)
chats = db.get_user_chats(ID)
print(f"User gefunden mit ID: {ID}")
print(f"Chats: {chats}")

'''
User gefunden mit ID: 1
Nachrichten: [(1, 'Hello World!', None)]
'''