import logging
import pytest
from aichat.domain.entities import User
from aichat.domain.services import ChatRoom, UserNotInChannelError
from aichat.ports.outbound import Notifier


class FakeNotifier(Notifier):
    def __init__(self):
        self.joined = []
        self.left = []
        self.messages = []

    def user_joined(self, user, channel_name):
        self.joined.append((user, channel_name))

    def user_left(self, user, channel_name):
        self.left.append((user, channel_name))

    def message_posted(self, message):
        self.messages.append(message)


@pytest.fixture
def notifier():
    return FakeNotifier()


@pytest.fixture
def room(notifier):
    return ChatRoom(notifier)


def test_post_message_notifies(room, notifier):
    user = room.connect("alice")
    room.post_message(user, ChatRoom.DEFAULT_CHANNEL, "hello")
    assert len(notifier.messages) == 1
    assert notifier.messages[0].text == "hello"


def test_join_notifies(room, notifier):
    user = room.connect("alice")
    assert (user, ChatRoom.DEFAULT_CHANNEL) in notifier.joined


def test_join_creates_channel_if_not_exists(room):
    user = User(nickname="alice")
    channel = room.join(user, "random")
    assert channel.has_member(user)
    assert "random" in room.list_channels()


def test_connect_joins_default_channel_automatically(room):
    user = room.connect("alice")
    default_channel = room._channels[ChatRoom.DEFAULT_CHANNEL]
    assert default_channel.has_member(user)


def test_connect_returns_unique_nickname_when_taken(room):
    first = room.connect("michal")
    second = room.connect("michal")
    third = room.connect("michal")
    assert first.nickname == "michal"
    assert second.nickname == "michal2"
    assert third.nickname == "michal3"


def test_post_message_outside_channel_raises_and_logs(room, caplog):
    user = room.connect("alice")
    room.leave(user, ChatRoom.DEFAULT_CHANNEL)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UserNotInChannelError):
            room.post_message(user, ChatRoom.DEFAULT_CHANNEL, "hello?")

    assert "alice" in caplog.text
    assert ChatRoom.DEFAULT_CHANNEL in caplog.text


def test_post_message_succeeds_after_joining(room):
    user = room.connect("alice")
    message = room.post_message(user, ChatRoom.DEFAULT_CHANNEL, "hello")
    assert message.text == "hello"


def test_leave_channel_where_not_member_is_noop(room):
    user = room.connect("alice")
    room.leave(user, "never-joined-this-one")


def test_leave_nonexistent_channel_is_noop(room):
    user = room.connect("alice")
    room.leave(user, "ghost-channel")


def test_disconnect_frees_nickname_for_reuse(room):
    user = room.connect("alice")
    room.disconnect(user)
    new_user = room.connect("alice")
    assert new_user.nickname == "alice"