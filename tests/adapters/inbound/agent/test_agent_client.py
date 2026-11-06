import asyncio
from types import SimpleNamespace

from aichat.adapters.inbound.agent.agent_client import AgentClient


class FakeAnthropic:
    def __init__(self, replies):
        self.replies, self.prompts = list(replies), []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.prompts.append(kw["messages"][0]["content"])
        return SimpleNamespace(content=[SimpleNamespace(text=self.replies.pop(0))])


class FakeWebSocket:
    async def send(self, _):
        pass


def make_client(monkeypatch, replies):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    client = AgentClient("ws://x")
    client._anthropic = FakeAnthropic(replies)
    client._websocket = FakeWebSocket()
    client._active_channel = "general"
    return client


def msg(text):
    return {"type": "message", "channel": "general", "from": "michal", "text": text}


def test_mention_reply_marks_earlier_unmentioned_messages_handled(monkeypatch):
    client = make_client(monkeypatch, ["4, and life is philosophical"])

    async def scenario():
        await client._handle_server_event(msg("what's the meaning of life?"))
        assert client._has_new_messages()
        await client._handle_server_event(msg("@claude what is 2+2?"))

    asyncio.run(scenario())
    # the cooldown loop would skip: nothing left to answer
    assert not client._has_new_messages()


def test_second_prompt_separates_handled_from_new(monkeypatch):
    client = make_client(monkeypatch, ["4", "green"])

    async def scenario():
        await client._handle_server_event(msg("@claude what is 2+2?"))
        await client._handle_server_event(msg("@claude blue + yellow?"))

    asyncio.run(scenario())
    first, second = client._anthropic.prompts
    earlier, new = second.split("New messages (respond only to these):")
    assert "what is 2+2?" in earlier and "claude: 4" in earlier
    assert "blue + yellow?" in new and "2+2" not in new


def test_no_reply_still_marks_messages_handled(monkeypatch):
    client = make_client(monkeypatch, ["NO_REPLY"])

    async def scenario():
        await client._handle_server_event(msg("hey"))
        await client._reply_now("general", forced=False)

    asyncio.run(scenario())
    assert not client._has_new_messages()


def test_message_arriving_mid_generation_stays_new(monkeypatch):
    client = make_client(monkeypatch, [])

    async def generate_while_message_arrives(history, forced):
        await client._handle_server_event(msg("late question"))
        return "early answer"

    client._generate_reply = generate_while_message_arrives

    async def scenario():
        await client._handle_server_event(msg("early question"))
        await client._reply_now("general", forced=False)

    asyncio.run(scenario())
    assert [(m.text, m.new) for m in client._history] == [
        ("early question", False),
        ("early answer", False),
        ("late question", True),
    ]
    assert client._has_new_messages()


def test_user_list_event_is_stored_and_put_in_system_prompt(monkeypatch):
    client = make_client(monkeypatch, ["3"])
    sent = []

    async def send(raw):
        sent.append(raw)

    client._websocket.send = send
    systems = []
    create = client._anthropic.messages.create
    client._anthropic.messages.create = lambda **kw: (systems.append(kw["system"]), create(**kw))[1]

    async def scenario():
        await client._handle_server_event({"type": "user_list", "users": ["claude", "claude2", "michal"]})
        await client._handle_server_event({"type": "user_joined", "nickname": "x", "channel": "general"})
        await client._handle_server_event(msg("@claude how many are there?"))

    asyncio.run(scenario())
    assert '"users"' in sent[0]  # join event triggers a refresh request
    assert "claude, claude2, michal" in systems[0]


def test_system_prompt_does_not_disown_a_suffixed_own_nickname(monkeypatch):
    client = make_client(monkeypatch, ["hi"])
    client._nickname = "claude2"
    systems = []
    create = client._anthropic.messages.create
    client._anthropic.messages.create = lambda **kw: (systems.append(kw["system"]), create(**kw))[1]

    asyncio.run(client._handle_server_event(msg("@claude2 hello")))
    assert "claude2 are other participants" not in systems[0]
    assert "Only the exact nickname claude2 is you" in systems[0]
