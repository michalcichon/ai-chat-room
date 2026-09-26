from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class User:
    nickname: str
    is_agent: bool = False

    def __post_init__(self):
        if not self.nickname.strip():
            raise ValueError("Nickname cannot be empty")


@dataclass(frozen=True)
class Message:
    author: User
    channel: str
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("Message text cannot be empty")
        if not self.channel.strip():
            raise ValueError("Channel cannot be empty")


@dataclass(frozen=False)
class Channel:
    name: str
    members: set[User] = field(default_factory=set)

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Channel name cannot be empty")

    def add_member(self, user: User) -> None:
        self.members.add(user)

    def remove_member(self, user: User) -> None:
        self.members.discard(user)

    def has_member(self, user: User) -> bool:
        return user in self.members
