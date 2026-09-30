from project import resolve_unique_nickname, is_mentioned, parse_command


def test_resolve_unique_nickname_returns_requested_when_free():
    assert resolve_unique_nickname("alice", set()) == "alice"


def test_resolve_unique_nickname_appends_suffix_when_taken():
    assert resolve_unique_nickname("alice", {"alice"}) == "alice2"


def test_resolve_unique_nickname_finds_first_free_suffix():
    assert resolve_unique_nickname("alice", {"alice", "alice2", "alice3"}) == "alice4"


def test_is_mentioned_true_for_exact_mention():
    assert is_mentioned("claude", "hey @claude, what do you think?") is True


def test_is_mentioned_false_when_not_mentioned():
    assert is_mentioned("claude", "hey everyone, what do you think?") is False


def test_is_mentioned_false_for_partial_nickname_match():
    assert is_mentioned("claude", "ask @claudexyz about it") is False


def test_parse_command_recognizes_join_with_argument():
    assert parse_command("/join random") == ("join", "random")


def test_parse_command_recognizes_commands_without_argument():
    assert parse_command("/leave") == ("leave", None)
    assert parse_command("/list") == ("list", None)
    assert parse_command("/quit") == ("quit", None)


def test_parse_command_treats_plain_text_as_message():
    assert parse_command("hello everyone") == ("message", "hello everyone")


def test_parse_command_treats_blank_input_as_empty():
    assert parse_command("   ") == ("empty", None)