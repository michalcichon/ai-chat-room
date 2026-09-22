import logging
import sys
from aichat.domain.entities import User


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
            print("\naichat> : Bye!")
            sys.exit()
        else:
            print(f"Welcome, {user.nickname}!")

    while True:
        try:
            prompt = input(f"{nickname} > : ")
        except KeyboardInterrupt:
            print("\naichat> : Bye!")
            sys.exit()
        logging.info("prompt=%s", prompt)
        

if __name__ == "__main__":
    main()