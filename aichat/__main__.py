import asyncio

from aichat.adapters.inbound.cli.terminal_client import TerminalClient

DEFAULT_SERVER_URI = "ws://localhost:8765"


def main():
    client = TerminalClient(DEFAULT_SERVER_URI)
    asyncio.run(client.run())


if __name__ == "__main__":
    main()