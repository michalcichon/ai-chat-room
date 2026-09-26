# aiChatRoom

#### Video Demo: tbd

#### Description

aiChatRoom is an IRC-inspired chat system written in Python. It lets users join channels, exchange messages, and switch between rooms using simple slash commands, all from the terminal. The project is built around a hexagonal (ports & adapters) architecture, keeping the core chat domain — users, channels, messages — fully decoupled from how it's accessed. Today that means a terminal client, but the same domain logic can be driven by other adapters (for example, an AI agent) without any changes to the core.

## Features

- Join and switch between channels (`/join <channel>`)
- Real-time-style message broadcasting within a channel
- Default channel (`#general`) on connect
- Clean separation between domain logic, use cases (ports), and delivery mechanisms (adapters)
- Fully tested domain layer (pytest)

## Architecture

The project follows a ports & adapters (hexagonal) structure:

```
aichat/
├── domain/          # Core entities and business rules (User, Channel, ChatRoom, Message, services)
├── ports/
│   ├── inbound/      # Use case interfaces the outside world calls into (e.g. ChatUseCase)
│   └── outbound/      # Interfaces the domain calls out to (e.g. Notifier)
└── adapters/
    └── inbound/
        └── cli/       # Terminal client — the current entry point
```

The `domain` package has no knowledge of *how* it's being used — whether by a human typing in a terminal or, in the future, by an AI agent through a separate adapter. New ways of interacting with the system are added as new adapters implementing the existing ports, without touching the domain.

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for dependency management and running the project

### Installation

```bash
git clone https://github.com/michalcichon/ai-chat-room.git
cd ai-chat-room
uv sync
```

### Running

```bash
uv run python -m aichat
```

You'll be prompted for a nickname, and dropped into the default `#general` channel.

### Usage

Once connected, type a message and hit enter to broadcast it to your current channel. Available commands:

| Command          | Description                     |
|------------------|----------------------------------|
| `/join <channel>` | Join (or switch to) a channel   |
| `Ctrl+C`          | Disconnect and exit             |

### Running tests

```bash
uv run pytest
```

## Project Structure Notes

- Uses [uv](https://github.com/astral-sh/uv) and `pyproject.toml` for dependency and environment management (no `requirements.txt`).
- Relies on Python's implicit namespace packages (PEP 420) — no `__init__.py` files scattered across the tree.
- Tests live in a top-level `tests/` directory, mirroring the `aichat` package structure, and import it as an installed (editable) package.

## Roadmap

- [ ] Additional inbound adapter for AI agents
- [ ] Persistent message history
- [ ] Private messaging between users