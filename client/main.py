# Implementation of GUI functions with server integration and error handling

class ChatApp:
    def __init__(self):
        self.chats = []
        self.active_chat = None

    def add_chat(self, chat_name):
        try:
            if chat_name not in self.chats:
                self.chats.append(chat_name)
                self.active_chat = chat_name
                print(f'Chat "{chat_name}" added successfully.')
            else:
                print(f'Chat "{chat_name}" already exists.')
        except Exception as e:
            print(f'Error adding chat: {e}')

    def switch_chat(self, chat_name):
        try:
            if chat_name in self.chats:
                self.active_chat = chat_name
                print(f'Switched to chat "{chat_name}".')
            else:
                print(f'Chat "{chat_name}" does not exist.')
        except Exception as e:
            print(f'Error switching chat: {e}')

    def send_message(self, message):
        try:
            if self.active_chat:
                # Simulates sending message to the server
                print(f'Sending message: "{message}" to chat "{self.active_chat}"')
                # Here you would include actual server integration logic
            else:
                print('Error: No active chat to send a message. Please switch to a chat.')
        except Exception as e:
            print(f'Error sending message: {e}')