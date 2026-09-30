import asyncio
import re

from aichat.adapters.inbound.cli.terminal_client import TerminalClient

DEFAULT_SERVER_URI = "ws://localhost:8765"


def main():
    client = TerminalClient(DEFAULT_SERVER_URI)
    asyncio.run(client.run())


def resolve_unique_nickname(requested: str, existing_nicknames: set[str]) -> str:
    """Return `requested` if it's free; otherwise the first `requestedN`
    (N starting at 2) that isn't already in `existing_nicknames`."""
    if requested not in existing_nicknames:
        return requested
    suffix = 2
    while f"{requested}{suffix}" in existing_nicknames:
        suffix += 1
    return f"{requested}{suffix}"


def is_mentioned(nickname: str, text: str) -> bool:
    """Return True if `text` contains an @-mention of `nickname` as a whole word
    (so "@claude" matches but "@claudexyz" does not)."""
    return re.search(rf"@{re.escape(nickname)}\b", text) is not None


def parse_command(raw_input: str) -> tuple[str, str | None]:
    """Parse a line of chat input into a (command, argument) tuple.

    Recognizes /join <channel>, /leave, /list, /help, /quit, and blank input;
    anything else is treated as a plain chat message.
    """
    text = raw_input.strip()
    if text == "":
        return ("empty", None)
    if text.startswith("/join "):
        return ("join", text.removeprefix("/join ").strip())
    if text == "/leave":
        return ("leave", None)
    if text == "/list":
        return ("list", None)
    if text == "/help":
        return ("help", None)
    if text == "/quit":
        return ("quit", None)
    return ("message", text)


if __name__ == "__main__":
    main()