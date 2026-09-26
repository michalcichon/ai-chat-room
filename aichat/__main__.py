from aichat.domain.services import ChatRoom
from aichat.adapters.outbound.console_notifier import ConsoleNotifier
from aichat.adapters.inbound.cli.terminal_client import TerminalClient


def main():
    notifier = ConsoleNotifier()
    room = ChatRoom(notifier)
    client = TerminalClient(room)
    client.run()


if __name__ == "__main__":
    main()