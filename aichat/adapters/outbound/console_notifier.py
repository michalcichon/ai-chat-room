from aichat.domain.entities import User, Message, Channel
from aichat.ports.outbound import Notifier


class ConsoleNotifier(Notifier):
    """Prints domain events to stdout. This is the CLI's outbound adapter."""

    def user_joined(self, user: User, channel: Channel) -> None:
        print(f"* {user.nickname} joined #{channel.name}")

    def user_left(self, user: User, channel: Channel) -> None:
        print(f"* {user.nickname} left #{channel.name}")

    def message_posted(self, message: Message, channel: Channel) -> None:
        print(f"[#{message.channel}] {message.author.nickname}: {message.text}")