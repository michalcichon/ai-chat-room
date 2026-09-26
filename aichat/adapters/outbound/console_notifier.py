from aichat.ports.outbound import Notifier


class ConsoleNotifier(Notifier):
    """Prints domain events to stdout. This is the CLI's outbound adapter."""

    def user_joined(self, user, channel_name):
        print(f"* {user.nickname} joined #{channel_name}")

    def user_left(self, user, channel_name):
        print(f"* {user.nickname} left #{channel_name}")

    def message_posted(self, message):
        print(f"[#{message.channel}] {message.author.nickname}: {message.text}")