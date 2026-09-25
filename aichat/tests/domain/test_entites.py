import pytest
from aichat.domain.entities import User


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