import logging
import sys
from aichat.domain.entities import User

AVAILABLE_COMMANDS = """
Available commands:
/join <channel>
/help
/quit
"""

def _quit():
    print("\naichat> : Bye!")
    sys.exit()


def _show_available_commands():
    print(AVAILABLE_COMMANDS)


def main():
    print("Welcome to aiChatRoom!\n")

    while True:
        try:
            nickname = input("Nickname: ")
            user = User(nickname)
            logging.info("user=%s", user)
            break
        except ValueError as error:
            print(f"Error: {error}...")
        except KeyboardInterrupt:
            _quit()
        else:
            print(f"Welcome, {user.nickname}!")

    while True:
        try:
            prompt = input(f"{user.nickname} > : ")
        except KeyboardInterrupt:
            _quit()
        else:
            logging.info("prompt=%s", prompt)
            if prompt == "/quit":
                _quit()
            elif prompt == "/help":
                _show_available_commands()
            elif prompt.startswith("/join "):
                channel = prompt.removeprefix("/join ")
                print(f"Joined {channel}")

        

if __name__ == "__main__":
    main()