import logging
from aichat.domain.entities import User, Channel, Message
from aichat.ports.outbound import Notifier

logger = logging.getLogger(__name__)


class UserNotInChannelError(Exception):
    pass


class ChatRoom:
    DEFAULT_CHANNEL = "general"

    def __init__(self, notifier: Notifier):
        self._channels: dict[str, Channel] = {}
        self._nicknames: set[str] = set()
        self._notifier = notifier

    def connect(self, requested_nickname: str, is_agent: bool = False) -> User:
        nickname = self._resolve_unique_nickname(requested_nickname)
        user = User(nickname=nickname, is_agent=is_agent)
        self._nicknames.add(nickname)
        self.join(user, self.DEFAULT_CHANNEL)
        return user

    def disconnect(self, user: User) -> None:
        self._nicknames.discard(user.nickname)
        for channel_name, channel in self._channels.items():
            if channel.has_member(user):
                channel.remove_member(user)
                self._notifier.user_left(user, channel_name)

    def join(self, user: User, channel_name: str) -> Channel:
        channel = self._channels.setdefault(channel_name, Channel(name=channel_name))
        channel.add_member(user)
        self._notifier.user_joined(user, channel_name)
        return channel

    def leave(self, user: User, channel_name: str) -> None:
        channel = self._channels.get(channel_name)
        if channel is None:
            return
        channel.remove_member(user)
        self._notifier.user_left(user, channel_name)

    def post_message(self, user: User, channel_name: str, text: str) -> Message:
        channel = self._channels.get(channel_name)
        if channel is None or not channel.has_member(user):
            logger.warning(
                "user=%s attempted to post in channel=%s without membership",
                user.nickname, channel_name,
            )
            raise UserNotInChannelError(f"You are not in #{channel_name}")

        message = Message(author=user, channel=channel_name, text=text)
        self._notifier.message_posted(message)
        return message

    def list_channels(self) -> list[str]:
        return list(self._channels.keys())

    def _resolve_unique_nickname(self, requested: str) -> str:
        if requested not in self._nicknames:
            return requested
        suffix = 2
        while f"{requested}{suffix}" in self._nicknames:
            suffix += 1
        return f"{requested}{suffix}"