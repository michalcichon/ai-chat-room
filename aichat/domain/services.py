import logging
from aichat.domain.entities import User, Channel, Message

logger = logging.getLogger(__name__)


class UserNotInChannelError(Exception):
    """Raised when a user tries to act in a channel they haven't joined."""


class ChatRoom:
    DEFAULT_CHANNEL = "general"

    def __init__(self):
        self._channels: dict[str, Channel] = {}
        self._nicknames: set[str] = set()

    def connect(self, requested_nickname: str) -> User:
        nickname = self._resolve_unique_nickname(requested_nickname)
        user = User(nickname=nickname)
        self._nicknames.add(nickname)
        self.join(user, self.DEFAULT_CHANNEL)
        return user

    def disconnect(self, user: User) -> None:
        self._nicknames.discard(user.nickname)
        for channel in self._channels.values():
            channel.remove_member(user)

    def join(self, user: User, channel_name: str) -> Channel:
        channel = self._channels.setdefault(channel_name, Channel(name=channel_name))
        channel.add_member(user)
        return channel

    def leave(self, user: User, channel_name: str) -> None:
        channel = self._channels.get(channel_name)
        if channel is None:
            return
        channel.remove_member(user)

    def post_message(self, user: User, channel_name: str, text: str) -> Message:
        channel = self._channels.get(channel_name)
        if channel is None or not channel.has_member(user):
            logger.warning(
                "user=%s attempted to post in channel=%s without membership",
                user.nickname,
                channel_name,
            )
            raise UserNotInChannelError(f"You are not in #{channel_name}")
        return Message(author=user, channel=channel_name, text=text)

    def list_channels(self) -> list[str]:
        return list(self._channels.keys())

    def _resolve_unique_nickname(self, requested: str) -> str:
        if requested not in self._nicknames:
            return requested
        suffix = 2
        while f"{requested}{suffix}" in self._nicknames:
            suffix += 1
        return f"{requested}{suffix}"