from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    nickname: str

    def __post_init__(self):
        if not self.nickname.strip():
            raise ValueError("Nickname cannot be empty")