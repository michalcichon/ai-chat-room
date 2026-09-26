import sys

from aichat.domain.services import ChatRoom, UserNotInChannelError

AVAILABLE_COMMANDS = """
Available commands:
/join <channel>   - join a channel and make it your active channel
/leave            - leave your current active channel
/list             - list all known channels
/help             - show this message
/quit             - exit the chat
"""

ERASE_PREVIOUS_LINE = "\x1b[1A\x1b[2K"

class TerminalClient:
    def __init__(self, room: ChatRoom):
        self._room = room
        self._user = None
        self._active_channel = None

    @staticmethod
    def _erase_last_terminal_line():
        if sys.stdout.isatty():
            sys.stdout.write(ERASE_PREVIOUS_LINE)
            sys.stdout.flush()
            
    def run(self):
        print("Welcome to aiChatRoom!\n")
        self._connect_user()

        while True:
            try:
                prompt = input(f"[#{self._active_channel}] {self._user.nickname}: ")
            except KeyboardInterrupt:
                self._quit()
            else:
                self._handle_input(prompt)

    def _connect_user(self):
        while True:
            try:
                nickname = input("Nickname: ")
                self._user = self._room.connect(nickname)
                self._active_channel = ChatRoom.DEFAULT_CHANNEL
                break
            except ValueError as error:
                print(f"Error: {error}...")
            except KeyboardInterrupt:
                self._quit()

    def _handle_input(self, prompt: str):
        if prompt == "/quit":
            self._quit()
        elif prompt == "/help":
            print(AVAILABLE_COMMANDS)
        elif prompt == "/list":
            channels = self._room.list_channels()
            print("Channels: " + ", ".join(channels))
        elif prompt.startswith("/join "):
            channel = prompt.removeprefix("/join ")
            self._room.join(self._user, channel)
            self._active_channel = channel
        elif prompt == "/leave":
            self._room.leave(self._user, self._active_channel)
        elif prompt.strip() == "":
            pass
        else:
            self._post_message(prompt)

    def _post_message(self, text: str):
        self._erase_last_terminal_line()
        try:
            self._room.post_message(self._user, self._active_channel, text)
        except UserNotInChannelError as error:
            print(f"Error: {error}")

    def _quit(self):
        print("\naichat> : Bye!")
        self._room.disconnect(self._user)
        sys.exit()