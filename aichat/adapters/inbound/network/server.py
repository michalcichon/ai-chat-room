import asyncio
import json
import logging
import os

import websockets

from aichat.domain.services import ChatRoom, UserNotInChannelError
from aichat.adapters.outbound.websocket_notifier import WebSocketNotifier

logger = logging.getLogger(__name__)

notifier = WebSocketNotifier()
chat_room = ChatRoom(notifier)


async def handler(websocket) -> None:
    user = None
    peer = websocket.remote_address
    try:
        async for raw in websocket:
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "connect":
                user = chat_room.connect(data["nickname"], is_agent=data.get("is_agent", False))
                notifier.register(user, websocket)
                logger.info("connected: %s (agent=%s) from %s", user.nickname, user.is_agent, peer)
                await websocket.send(json.dumps({
                    "type": "connected",
                    "nickname": user.nickname,
                    "default_channel": chat_room.default_channel,
                }))

            elif msg_type == "join":
                chat_room.join(user, data["channel"])
                logger.info("%s joined #%s", user.nickname, data["channel"])

            elif msg_type == "leave":
                chat_room.leave(user, data["channel"])
                logger.info("%s left #%s", user.nickname, data["channel"])

            elif msg_type == "list":
                channels = chat_room.list_channels()
                logger.debug("%s requested channel list (%d channels)", user.nickname, len(channels))
                await websocket.send(json.dumps({
                    "type": "channel_list",
                    "channels": channels,
                }))

            elif msg_type == "message":
                try:
                    chat_room.post_message(user, data["channel"], data["text"])
                    logger.debug("%s -> #%s: %s", user.nickname, data["channel"], data["text"])
                except UserNotInChannelError as e:
                    logger.warning("%s tried to post in #%s without membership",
                                   user.nickname, data["channel"])
                    await websocket.send(json.dumps({"type": "error", "message": str(e)}))

            else:
                logger.warning("unknown message type %r from %s", msg_type, peer)

    except websockets.ConnectionClosed:
        logger.info("connection closed: %s", user.nickname if user else peer)
    except Exception:
        logger.exception("unhandled error in connection handler for %s", peer)
    finally:
        if user is not None:
            chat_room.disconnect(user)
            notifier.unregister(user)
            logger.info("disconnected: %s", user.nickname)


async def main(host: str = "localhost", port: int = 8765) -> None:
    log_level = os.environ.get("AICHAT_SERVER_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(message)s")

    async with websockets.serve(handler, host, port):
        logger.info("serving on ws://%s:%d", host, port)
        await asyncio.Future()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()