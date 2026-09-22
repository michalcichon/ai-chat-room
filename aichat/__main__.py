import logging
import sys

from aichat.domain.entities import User

def main():
    print("Welcome to aiChatRoom!\n")
    nickname = input("Nickname: ")
    user = User(nickname)
    logging.info("user=%s", user)

    while True:
        try:
            prompt = input(f"{nickname} > : ")
        except KeyboardInterrupt:
            print("\naichat> : Bye!")
            sys.exit()
        # print(f"{nickname} > : {prompt}")
        logging.info("prompt=%s", prompt)
        

if __name__ == "__main__":
    main()