import asyncio
import json
import logging
import os
import re
import time

import websockets
from anthropic import Anthropic

MODEL = "claude-haiku-4-5"
HISTORY_LIMIT = 20
NO_REPLY_SENTINEL = "NO_REPLY"
SPONTANEOUS_REPLY_COOLDOWN_SECONDS = 30

logger = logging.getLogger(__name__)


class AgentClient:
    """AI agent adapter: connects like a normal client. Always replies when
    directly mentioned (@nickname); optionally also decides for itself
    whether to chime in spontaneously, throttled to avoid spamming."""

    def __init__(
        self,
        uri: str,
        nickname: str = "claude",
        mentions_only: bool = False,
    ):
        self._uri = uri
        self._nickname = nickname
        self._mentions_only = mentions_only
        self._active_channel = None
        self._websocket = None
        self._anthropic = Anthropic()
        self._history: list[dict] = []
        self._last_spontaneous_reply_at: float = 0.0

    async def run(self):
        try:
            async with websockets.connect(self._uri) as websocket:
                self._websocket = websocket
                await self._connect()
                mode = "mentions-only" if self._mentions_only else "spontaneous + mentions"
                logger.info("connected as %s, listening on #%s (%s)",
                            self._nickname, self._active_channel, mode)
                async for raw in websocket:
                    await self._handle_server_event(json.loads(raw))
        except OSError:
            logger.error("could not connect to server at %s", self._uri)

    async def _connect(self):
        await self._websocket.send(json.dumps({
            "type": "connect", "nickname": self._nickname, "is_agent": True,
        }))
        reply = json.loads(await self._websocket.recv())
        if reply["type"] == "error":
            raise RuntimeError(f"Failed to connect: {reply['message']}")
        self._nickname = reply["nickname"]
        self._active_channel = reply["default_channel"]

    def _is_mentioned(self, text: str) -> bool:
        return re.search(rf"@{re.escape(self._nickname)}\b", text) is not None

    def _spontaneous_reply_on_cooldown(self) -> bool:
        return (time.monotonic() - self._last_spontaneous_reply_at) < SPONTANEOUS_REPLY_COOLDOWN_SECONDS

    async def _handle_server_event(self, data: dict):
        if data.get("type") != "message" or data["from"] == self._nickname:
            return

        self._history.append({"from": data["from"], "text": data["text"]})
        self._history = self._history[-HISTORY_LIMIT:]

        forced = self._is_mentioned(data["text"])

        if not forced:
            if self._mentions_only:
                logger.debug("message from %s skipped (mentions-only mode, not mentioned)",
                             data["from"])
                return
            if self._spontaneous_reply_on_cooldown():
                remaining = SPONTANEOUS_REPLY_COOLDOWN_SECONDS - (time.monotonic() - self._last_spontaneous_reply_at)
                logger.debug("message from %s skipped (cooldown, %.0fs remaining)",
                             data["from"], remaining)
                return

        try:
            reply_text = await self._generate_reply(forced=forced)
        except Exception:
            logger.exception("failed to generate reply")
            return

        if reply_text is None:
            logger.debug("decided not to reply to %s", data["from"])
            return

        logger.debug("decided to reply to %s (%s)",
                      data["from"], "mentioned" if forced else "spontaneous")

        if not forced:
            self._last_spontaneous_reply_at = time.monotonic()

        await self._websocket.send(json.dumps({
            "type": "message", "channel": data["channel"], "text": reply_text,
        }))

    async def _generate_reply(self, forced: bool) -> str | None:
        conversation = "\n".join(f"{m['from']}: {m['text']}" for m in self._history)

        if forced:
            decision_rule = "You have just been directly mentioned, so you must always reply."
        else:
            decision_rule = (
                f"Reply only if you would genuinely be helpful or add something to the "
                f"conversation. If you don't have anything worth saying, respond with "
                f"exactly the single word {NO_REPLY_SENTINEL} and nothing else."
            )

        response = await asyncio.to_thread(
            self._anthropic.messages.create,
            model=MODEL,
            max_tokens=300,
            system=(
                f"You are a participant in a chat room with the nickname {self._nickname}. "
                "Reply briefly and naturally, like in a chat conversation, "
                "not like an AI assistant. Don't reintroduce yourself. "
                + decision_rule
            ),
            messages=[{"role": "user", "content": conversation}],
        )
        text = response.content[0].text.strip()
        if not forced and text == NO_REPLY_SENTINEL:
            return None
        return text


async def main():
    log_level = os.environ.get("AICHAT_AGENT_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(message)s")

    uri = os.environ.get("AICHAT_SERVER_URI", "ws://localhost:8765")
    nickname = os.environ.get("AICHAT_AGENT_NICKNAME", "claude")
    mentions_only = os.environ.get("AICHAT_AGENT_MENTIONS_ONLY", "false").lower() == "true"
    await AgentClient(uri, nickname, mentions_only=mentions_only).run()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()