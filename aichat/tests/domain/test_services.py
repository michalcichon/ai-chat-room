import logging
import pytest
from aichat.domain.entities import User
from aichat.domain.services import ChatRoom, UserNotInChannelError


def test_join_creates_channel_if_not_exists():
    room = ChatRoom()
    user = User(nickname="alice")
    channel = room.join(user, "random")
    assert channel.has_member(user)
    assert "random" in room.list_channels()


def test_connect_joins_default_channel_automatically():
    room = ChatRoom()
    user = room.connect("alice")
    default_channel = room._channels[ChatRoom.DEFAULT_CHANNEL]
    assert default_channel.has_member(user)


def test_connect_returns_unique_nickname_when_taken():
    room = ChatRoom()
    first = room.connect("michal")
    second = room.connect("michal")
    third = room.connect("michal")
    assert first.nickname == "michal"
    assert second.nickname == "michal2"
    assert third.nickname == "michal3"


def test_post_message_outside_channel_raises_and_logs(caplog):
    room = ChatRoom()
    user = room.connect("alice")
    room.leave(user, ChatRoom.DEFAULT_CHANNEL)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UserNotInChannelError):
            room.post_message(user, ChatRoom.DEFAULT_CHANNEL, "hello?")

    assert "alice" in caplog.text
    assert ChatRoom.DEFAULT_CHANNEL in caplog.text


def test_post_message_succeeds_after_joining():
    room = ChatRoom()
    user = room.connect("alice")
    message = room.post_message(user, ChatRoom.DEFAULT_CHANNEL, "hello")
    assert message.text == "hello"


def test_leave_channel_where_not_member_is_noop():
    room = ChatRoom()
    user = room.connect("alice")
    room.leave(user, "never-joined-this-one")


def test_leave_nonexistent_channel_is_noop():
    room = ChatRoom()
    user = room.connect("alice")
    room.leave(user, "ghost-channel")


def test_disconnect_frees_nickname_for_reuse():
    room = ChatRoom()
    user = room.connect("alice")
    room.disconnect(user)
    new_user = room.connect("alice")
    assert new_user.nickname == "alice"