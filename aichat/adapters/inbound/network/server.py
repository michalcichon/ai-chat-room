import asyncio
import json
import websockets

from aichat.domain.services import ChatRoom, UserNotInChannelError
from aichat.adapters.outbound.websocket_notifier import WebSocketNotifier

notifier = WebSocketNotifier()
chat_room = ChatRoom(notifier)


async def handler(websocket) -> None:
    user = None
    try:
        async for raw in websocket:
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "connect":
                user = chat_room.connect(data["nickname"], is_agent=data.get("is_agent", False))
                notifier.register(user, websocket)
                await websocket.send(json.dumps({
                    "type": "connected",
                    "nickname": user.nickname,
                    "default_channel": chat_room.default_channel,
                }))

            elif msg_type == "join":
                chat_room.join(user, data["channel"])

            elif msg_type == "leave":
                chat_room.leave(user, data["channel"])

            elif msg_type == "list":
                await websocket.send(json.dumps({
                    "type": "channel_list",
                    "channels": chat_room.list_channels(),
                }))

            elif msg_type == "message":
                try:
                    chat_room.post_message(user, data["channel"], data["text"])
                except UserNotInChannelError as e:
                    await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    finally:
        if user is not None:
            chat_room.disconnect(user)
            notifier.unregister(user)


async def main(host: str = "localhost", port: int = 8765) -> None:
    async with websockets.serve(handler, host, port):
        print(f"Serving on ws://{host}:{port}")
        await asyncio.Future()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())