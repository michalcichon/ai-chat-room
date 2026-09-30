import asyncio
import json

from aichat.domain.entities import User, Message, Channel
from aichat.ports.outbound import Notifier


class WebSocketNotifier(Notifier):
    """Sends domain events to connected clients over WebSocket."""

    def __init__(self) -> None:
        self._connections: dict[str, object] = {}  # nickname -> websocket

    def register(self, user: User, connection) -> None:
        self._connections[user.nickname] = connection

    def unregister(self, user: User) -> None:
        self._connections.pop(user.nickname, None)

    def user_joined(self, user: User, channel: Channel) -> None:
        self._broadcast(channel, {
            "type": "user_joined", "nickname": user.nickname, "channel": channel.name,
        })

    def user_left(self, user: User, channel: Channel) -> None:
        self._broadcast(channel, {
            "type": "user_left", "nickname": user.nickname, "channel": channel.name,
        })

    def message_posted(self, message: Message, channel: Channel) -> None:
        self._broadcast(channel, {
            "type": "message",
            "channel": message.channel,
            "from": message.author.nickname,
            "text": message.text,
        })

    def _broadcast(self, channel: Channel, payload: dict) -> None:
        data = json.dumps(payload)
        for user in channel.members:
            connection = self._connections.get(user.nickname)
            if connection is not None:
                asyncio.create_task(connection.send(data))