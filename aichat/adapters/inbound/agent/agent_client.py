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
    """AI agent adapter: connects like a normal client. Always replies
    immediately when directly mentioned (@nickname). Otherwise, every
    SPONTANEOUS_REPLY_COOLDOWN_SECONDS it checks whether anything happened
    on the channel since its last check, and if so, decides once whether
    to chime in."""

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
        self._unseen_since_last_check = False

    async def run(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            logger.error(
                "ANTHROPIC_API_KEY is not set. Get a key from console.anthropic.com "
                "and run: export ANTHROPIC_API_KEY=sk-ant-..."
            )
            return

        try:
            async with websockets.connect(self._uri) as websocket:
                self._websocket = websocket
                await self._connect()
                mode = "mentions-only" if self._mentions_only else "spontaneous + mentions"
                logger.info("connected as %s, listening on #%s (%s)",
                            self._nickname, self._active_channel, mode)

                cooldown_task = None
                if not self._mentions_only:
                    cooldown_task = asyncio.create_task(self._cooldown_loop())

                try:
                    async for raw in websocket:
                        await self._handle_server_event(json.loads(raw))
                finally:
                    if cooldown_task is not None:
                        cooldown_task.cancel()
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

    async def _handle_server_event(self, data: dict):
        if data.get("type") != "message" or data["from"] == self._nickname:
            return

        self._history.append({"from": data["from"], "text": data["text"]})
        self._history = self._history[-HISTORY_LIMIT:]

        if self._is_mentioned(data["text"]):
            await self._reply_now(data["channel"], forced=True)
            return

        if self._mentions_only:
            logger.debug("message from %s skipped (mentions-only mode, not mentioned)",
                         data["from"])
            return

        self._unseen_since_last_check = True
        logger.debug("message from %s queued for consideration at next cooldown check",
                     data["from"])

    async def _cooldown_loop(self):
        """Wakes up every cooldown interval and decides at most once per
        interval whether to chime in, based on messages received since the
        last check. Makes zero API calls when nothing new happened."""
        while True:
            await asyncio.sleep(SPONTANEOUS_REPLY_COOLDOWN_SECONDS)

            if not self._unseen_since_last_check:
                logger.debug("cooldown elapsed, nothing new since last check, skipping")
                continue

            self._unseen_since_last_check = False
            channel = self._active_channel
            await self._reply_now(channel, forced=False)

    async def _reply_now(self, channel: str, forced: bool):
        try:
            reply_text = await self._generate_reply(forced=forced)
        except Exception:
            logger.exception("failed to generate reply")
            return

        if reply_text is None:
            logger.debug("decided not to reply (%s)", "mentioned" if forced else "spontaneous check")
            return

        logger.debug("decided to reply (%s)", "mentioned" if forced else "spontaneous check")
        await self._websocket.send(json.dumps({
            "type": "message", "channel": channel, "text": reply_text,
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