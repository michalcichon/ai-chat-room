import asyncio
import json
import sys

import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

AVAILABLE_COMMANDS = """
Available commands:
/join <channel>   - join a channel and make it your active channel
/leave            - leave your current active channel
/list             - list all known channels
/help             - show this message
/quit             - exit the chat
"""


class TerminalClient:
    def __init__(self, uri: str):
        self._uri = uri
        self._websocket = None
        self._nickname = None
        self._active_channel = None
        self._list_response: asyncio.Future | None = None
        self._session = PromptSession()

    async def run(self):
        print("Welcome to aiChatRoom!\n")
        try:
            async with websockets.connect(self._uri) as websocket:
                self._websocket = websocket
                with patch_stdout():
                    await self._connect_user()

                    listener = asyncio.create_task(self._listen())
                    try:
                        await self._input_loop()
                    finally:
                        listener.cancel()
        except OSError:
            print(f"Could not connect to the server at {self._uri}.")
            print("Is the server running? Try: uv run aichat-server")

    async def _connect_user(self):
        while True:
            nickname = await self._session.prompt_async("Nickname: ")
            await self._websocket.send(json.dumps({"type": "connect", "nickname": nickname}))
            reply = json.loads(await self._websocket.recv())
            if reply["type"] == "error":
                print(f"Error: {reply['message']}")
                continue
            self._nickname = reply["nickname"]
            self._active_channel = reply["default_channel"]
            break

    async def _input_loop(self):
        while True:
            prompt_text = f"[#{self._active_channel}] {self._nickname}: "
            try:
                prompt = await self._session.prompt_async(prompt_text)
            except (KeyboardInterrupt, EOFError):
                await self._quit()
                return
            await self._handle_input(prompt)

    async def _listen(self):
        try:
            async for raw in self._websocket:
                await self._handle_server_event(json.loads(raw))
        except websockets.ConnectionClosed:
            pass

    async def _handle_server_event(self, data: dict):
        if data.get("type") == "channel_list":
            if self._list_response is not None and not self._list_response.done():
                self._list_response.set_result(data["channels"])
            return

        if data["type"] == "user_joined":
            print(f"* {data['nickname']} joined #{data['channel']}")
        elif data["type"] == "user_left":
            print(f"* {data['nickname']} left #{data['channel']}")
        elif data["type"] == "message":
            if data["from"] != self._nickname:
                print(f"[#{data['channel']}] {data['from']}: {data['text']}")
        elif data["type"] == "error":
            print(f"Error: {data['message']}")

    async def _handle_input(self, prompt: str):
        if prompt == "/quit":
            await self._quit()
        elif prompt == "/help":
            print(AVAILABLE_COMMANDS)
        elif prompt == "/list":
            await self._list_channels()
        elif prompt.startswith("/join "):
            channel = prompt.removeprefix("/join ")
            await self._websocket.send(json.dumps({"type": "join", "channel": channel}))
            self._active_channel = channel
        elif prompt == "/leave":
            await self._websocket.send(json.dumps({"type": "leave", "channel": self._active_channel}))
        elif prompt.strip() == "":
            pass
        else:
            await self._post_message(prompt)

    async def _list_channels(self):
        self._list_response = asyncio.get_event_loop().create_future()
        await self._websocket.send(json.dumps({"type": "list"}))
        channels = await self._list_response
        print("Channels: " + ", ".join(channels))

    async def _post_message(self, text: str):
        await self._websocket.send(json.dumps({
            "type": "message", "channel": self._active_channel, "text": text,
        }))

    async def _quit(self):
        print("\naichat> : Bye!")
        await self._websocket.close()
        sys.exit()