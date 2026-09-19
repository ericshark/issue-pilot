"""Tests for the chat tool loop, with the Anthropic client replaced by a fake.

Each scripted ``Message`` is what one ``messages.stream`` call returns; the
fake yields its text blocks as the stream and records every request so the
tests can inspect the replayed conversation.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from anthropic.types import Message, MessageParam, TextBlock, ToolUseBlock, Usage

from app.ai import chat
from app.ai.chat import MAX_TOOL_ROUNDS, ChatUnavailable, stream_reply


def message(
    *blocks: TextBlock | ToolUseBlock, stop_reason: str = "end_turn"
) -> Message:
    return Message.model_construct(
        id="msg_1",
        type="message",
        role="assistant",
        model="test-model",
        content=list(blocks),
        stop_reason=stop_reason,
        stop_sequence=None,
        usage=Usage(input_tokens=1, output_tokens=1),
    )


def text(value: str) -> TextBlock:
    return TextBlock(type="text", text=value)


def tool_use(name: str, **input: Any) -> ToolUseBlock:
    return ToolUseBlock(type="tool_use", id=f"toolu_{name}", name=name, input=input)


class FakeStream:
    def __init__(self, result: Message) -> None:
        self.result = result

    def __enter__(self) -> "FakeStream":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    @property
    def text_stream(self) -> Iterator[str]:
        for block in self.result.content:
            if isinstance(block, TextBlock):
                yield block.text

    def get_final_message(self) -> Message:
        return self.result


class FakeMessages:
    def __init__(self, script: list[Message]) -> None:
        self.script = list(script)
        self.requests: list[dict[str, Any]] = []

    def stream(self, **request: Any) -> FakeStream:
        self.requests.append(request)
        return FakeStream(self.script.pop(0))


class FakeClient:
    def __init__(self, script: list[Message]) -> None:
        self.messages = FakeMessages(script)


@pytest.fixture
def scripted(monkeypatch: pytest.MonkeyPatch):
    """Install a fake client that answers ``messages.stream`` from a script."""

    def install(script: list[Message]) -> FakeClient:
        client = FakeClient(script)
        monkeypatch.setattr(chat, "get_client", lambda: client)
        return client

    return install


HISTORY: list[MessageParam] = [{"role": "user", "content": "Hi"}]


def test_plain_text_reply_is_streamed(scripted) -> None:
    scripted([message(text("Hello "), text("there"))])

    assert list(stream_reply(HISTORY)) == [("text", "Hello "), ("text", "there")]


def test_tool_round_trip_replays_call_and_result(scripted, monkeypatch) -> None:
    monkeypatch.setattr(chat, "execute_tool", lambda name, raw: ('{"id": 1}', False))
    client = scripted(
        [
            message(
                text("Checking."),
                tool_use("get_issue", issue_id=1),
                stop_reason="tool_use",
            ),
            message(text("Issue #1 is open.")),
        ]
    )

    events = list(stream_reply(HISTORY))

    assert events == [
        ("text", "Checking."),
        ("tool", {"name": "get_issue", "input": {"issue_id": 1}}),
        # A blank line separates text from before and after the tool call.
        ("text", "\n\n"),
        ("text", "Issue #1 is open."),
    ]
    second_request = client.messages.requests[1]["messages"]
    assert second_request[0] == {"role": "user", "content": "Hi"}
    assert second_request[1]["role"] == "assistant"
    assert second_request[2] == {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "toolu_get_issue",
                "content": '{"id": 1}',
                "is_error": False,
            }
        ],
    }


def test_refusal_and_truncation_raise(scripted) -> None:
    scripted([message(text("partial"), stop_reason="refusal")])
    with pytest.raises(ChatUnavailable, match="declined"):
        list(stream_reply(HISTORY))

    scripted([message(text("partial"), stop_reason="max_tokens")])
    with pytest.raises(ChatUnavailable, match="too long"):
        list(stream_reply(HISTORY))


def test_empty_reply_raises(scripted) -> None:
    scripted([message()])

    with pytest.raises(ChatUnavailable, match="empty"):
        list(stream_reply(HISTORY))


def test_tool_loop_is_bounded(scripted, monkeypatch) -> None:
    monkeypatch.setattr(chat, "execute_tool", lambda name, raw: ("{}", False))
    looping = message(tool_use("list_issues", limit=10), stop_reason="tool_use")
    client = scripted([looping] * (MAX_TOOL_ROUNDS + 2))

    with pytest.raises(ChatUnavailable, match="too many tool calls"):
        list(stream_reply(HISTORY))

    assert len(client.messages.requests) == MAX_TOOL_ROUNDS + 1


def test_history_is_trimmed_to_recent_user_led_turns(scripted) -> None:
    client = scripted([message(text("ok"))])
    long_history: list[MessageParam] = []
    for index in range(chat.MAX_HISTORY_MESSAGES + 3):
        role = "assistant" if index % 2 else "user"
        long_history.append({"role": role, "content": str(index)})
    # Ends on a user turn; the oldest kept message must also be a user turn.

    list(stream_reply(long_history))

    sent = client.messages.requests[0]["messages"]
    assert len(sent) <= chat.MAX_HISTORY_MESSAGES
    assert sent[0]["role"] == "user"
    assert sent[-1] == long_history[-1]


def test_missing_api_key_raises_before_streaming() -> None:
    with pytest.raises(ChatUnavailable, match="ANTHROPIC_API_KEY"):
        list(stream_reply(HISTORY))
