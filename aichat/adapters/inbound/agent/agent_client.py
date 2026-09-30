import asyncio
import json
import os

import websockets
from anthropic import Anthropic

MODEL = "claude-haiku-4-5"
HISTORY_LIMIT = 20


class AgentClient:
    """AI agent adapter: connects like a normal client, but replies via
    the Claude API only when directly mentioned (@nickname) on a channel."""

    def __init__(self, uri: str, nickname: str = "claude"):
        self._uri = uri
        self._nickname = nickname
        self._active_channel = None
        self._websocket = None
        self._anthropic = Anthropic()
        self._history: list[dict] = []

    async def run(self):
        async with websockets.connect(self._uri) as websocket:
            self._websocket = websocket
            await self._connect()
            print(f"[agent:{self._nickname}] connected, listening on #{self._active_channel}")
            async for raw in websocket:
                await self._handle_server_event(json.loads(raw))

    async def _connect(self):
        await self._websocket.send(json.dumps({
            "type": "connect", "nickname": self._nickname, "is_agent": True,
        }))
        reply = json.loads(await self._websocket.recv())
        if reply["type"] == "error":
            raise RuntimeError(f"Failed to connect: {reply['message']}")
        self._nickname = reply["nickname"]
        self._active_channel = reply["default_channel"]

    async def _handle_server_event(self, data: dict):
        if data.get("type") != "message":
            return

        self._history.append({"from": data["from"], "text": data["text"]})
        self._history = self._history[-HISTORY_LIMIT:]

        mention = f"@{self._nickname}"
        if mention not in data["text"] or data["from"] == self._nickname:
            return

        reply_text = await self._generate_reply()
        await self._websocket.send(json.dumps({
            "type": "message", "channel": data["channel"], "text": reply_text,
        }))

    async def _generate_reply(self) -> str:
        conversation = "\n".join(f"{m['from']}: {m['text']}" for m in self._history)
        response = await asyncio.to_thread(
            self._anthropic.messages.create,
            model=MODEL,
            max_tokens=300,
            system=(
                f"You are a participant in a chat room with the nickname {self._nickname}. "
                "Reply briefly and naturally, like in a chat conversation, "
                "not like an AI assistant. Don't reintroduce yourself."
            ),
            messages=[{"role": "user", "content": conversation}],
        )
        return response.content[0].text


async def main():
    uri = os.environ.get("AICHAT_SERVER_URI", "ws://localhost:8765")
    nickname = os.environ.get("AICHAT_AGENT_NICKNAME", "claude")
    await AgentClient(uri, nickname).run()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()