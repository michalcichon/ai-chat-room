import logging
import sys

def main():
    print("Welcome to aiChatRoom!\n")
    nickname = input("Nickname: ")

    while True:
        try:
            prompt = input(f"{nickname} > : ")
        except KeyboardInterrupt:
            print("\naichat> : Bye!")
            sys.exit()
        # print(f"{nickname} > : {prompt}")
        logging.info(f"prompt={prompt}")
        

if __name__ == "__main__":
    main()