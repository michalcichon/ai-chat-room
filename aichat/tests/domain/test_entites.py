from datetime import timezone

import pytest
from aichat.domain.entities import User, Channel, Message


def test_user_created_with_valid_nickname():
    user = User(nickname="alice")
    assert user.nickname == "alice"


def test_user_raises_on_empty_nickname():
    with pytest.raises(ValueError):
        User(nickname="")


def test_user_raises_on_whitespace_only_nickname():
    with pytest.raises(ValueError):
        User(nickname="   ")


def test_user_is_immutable():
    user = User(nickname="alice")
    with pytest.raises(AttributeError):
        user.nickname = "bob"


def test_user_is_hashable():
    user = User(nickname="alice")
    assert hash(user) is not None


def test_channel_starts_empty():
    channel = Channel(name="general")
    assert channel.members == set()


def test_add_member_adds_user():
    channel = Channel(name="general")
    user = User(nickname="alice")
    channel.add_member(user)
    assert channel.has_member(user)


def test_add_member_is_idempotent():
    channel = Channel(name="general")
    user = User(nickname="alice")
    channel.add_member(user)
    channel.add_member(user)
    assert len(channel.members) == 1


def test_remove_member_that_never_joined_does_not_raise():
    channel = Channel(name="general")
    user = User(nickname="alice")
    channel.remove_member(user)


def test_message_created_with_valid_data():
    user = User(nickname="alice")
    message = Message(author=user, channel="general", text="hello")
    assert message.text == "hello"
    assert message.channel == "general"
    assert message.author == user


def test_message_raises_on_empty_text():
    user = User(nickname="alice")
    with pytest.raises(ValueError):
        Message(author=user, channel="general", text="   ")


def test_message_raises_on_empty_channel():
    user = User(nickname="alice")
    with pytest.raises(ValueError):
        Message(author=user, channel="", text="hello")


def test_message_has_utc_timestamp_by_default():
    user = User(nickname="alice")
    message = Message(author=user, channel="general", text="hello")
    assert message.timestamp.tzinfo == timezone.utc


def test_message_is_immutable():
    user = User(nickname="alice")
    message = Message(author=user, channel="general", text="hello")
    with pytest.raises(AttributeError):
        message.text = "changed"