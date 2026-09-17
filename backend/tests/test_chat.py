"""Contract tests for the chat endpoints, with Claude replaced by a stub."""

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.ai.chat import ChatUnavailable
from app.routes import chat as chat_routes


def parse_sse(body: str) -> list[tuple[str, dict]]:
    """Turn a raw SSE body into ``(event, data)`` pairs."""

    events: list[tuple[str, dict]] = []
    for block in body.strip().split("\n\n"):
        event = ""
        data = ""
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[len("event: ") :]
            elif line.startswith("data: "):
                data = line[len("data: ") :]
        events.append((event, json.loads(data)))
    return events


def send(
    client: TestClient, conversation_id: int, content: str
) -> list[tuple[str, dict]]:
    response = client.post(
        f"/api/chat/conversations/{conversation_id}/messages", json={"content": content}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    return parse_sse(response.text)


@pytest.fixture
def stub_reply(monkeypatch: pytest.MonkeyPatch) -> list[list[dict[str, str]]]:
    """Stream a fixed two-chunk reply and record the history sent."""

    calls: list[list[dict[str, str]]] = []

    def fake_stream_reply(history: list[dict[str, str]]) -> Iterator[tuple]:
        calls.append(history)
        yield "text", "Stubbed "
        yield "text", "reply"

    monkeypatch.setattr(chat_routes, "ensure_configured", lambda: None)
    monkeypatch.setattr(chat_routes, "stream_reply", fake_stream_reply)
    return calls


def test_create_conversation_starts_untitled(client: TestClient) -> None:
    response = client.post("/api/chat/conversations")

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "title": "New chat",
        "created_at": response.json()["created_at"],
    }
    assert response.json()["created_at"].endswith("Z")


def test_send_message_stores_both_turns_and_titles_conversation(
    client: TestClient, stub_reply: list[list[dict[str, str]]]
) -> None:
    conversation_id = client.post("/api/chat/conversations").json()["id"]

    events = send(client, conversation_id, "  What is IssuePilot?  ")

    assert [event for event, _ in events] == ["delta", "delta", "done"]
    assert [data["text"] for event, data in events if event == "delta"] == [
        "Stubbed ",
        "reply",
    ]
    body = events[-1][1]
    assert body["user_message"]["role"] == "user"
    assert body["user_message"]["content"] == "What is IssuePilot?"
    assert body["assistant_message"]["role"] == "assistant"
    assert body["assistant_message"]["content"] == "Stubbed reply"
    assert stub_reply == [[{"role": "user", "content": "What is IssuePilot?"}]]

    detail = client.get(f"/api/chat/conversations/{conversation_id}").json()
    assert detail["title"] == "What is IssuePilot?"
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]


def test_send_message_passes_full_history_in_order(
    client: TestClient, stub_reply: list[list[dict[str, str]]]
) -> None:
    conversation_id = client.post("/api/chat/conversations").json()["id"]
    client.post(
        f"/api/chat/conversations/{conversation_id}/messages", json={"content": "One"}
    )
    client.post(
        f"/api/chat/conversations/{conversation_id}/messages", json={"content": "Two"}
    )

    assert stub_reply[-1] == [
        {"role": "user", "content": "One"},
        {"role": "assistant", "content": "Stubbed reply"},
        {"role": "user", "content": "Two"},
    ]


def test_long_first_message_is_truncated_into_title(
    client: TestClient, stub_reply: list[list[dict[str, str]]]
) -> None:
    conversation_id = client.post("/api/chat/conversations").json()["id"]
    send(client, conversation_id, "x" * 100)

    title = client.get(f"/api/chat/conversations/{conversation_id}").json()["title"]
    assert len(title) == 60
    assert title.endswith("…")


def test_list_conversations_returns_newest_first(client: TestClient) -> None:
    first = client.post("/api/chat/conversations").json()
    second = client.post("/api/chat/conversations").json()

    response = client.get("/api/chat/conversations")

    assert response.status_code == 200
    assert response.json()["items"] == [second, first]


def test_mid_stream_failure_emits_error_and_stores_nothing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_stream_reply(history: list[dict[str, str]]) -> Iterator[tuple]:
        yield "text", "partial"
        raise ChatUnavailable("Could not reach the Claude API.")

    monkeypatch.setattr(chat_routes, "ensure_configured", lambda: None)
    monkeypatch.setattr(chat_routes, "stream_reply", failing_stream_reply)
    conversation_id = client.post("/api/chat/conversations").json()["id"]

    events = send(client, conversation_id, "Hi")

    assert events == [
        ("delta", {"text": "partial"}),
        ("error", {"detail": "Could not reach the Claude API."}),
    ]
    assert (
        client.get(f"/api/chat/conversations/{conversation_id}").json()["messages"]
        == []
    )


def test_missing_api_key_is_a_plain_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unconfigured() -> None:
        raise ChatUnavailable("ANTHROPIC_API_KEY is not configured on the server.")

    monkeypatch.setattr(chat_routes, "ensure_configured", unconfigured)
    conversation_id = client.post("/api/chat/conversations").json()["id"]

    response = client.post(
        f"/api/chat/conversations/{conversation_id}/messages", json={"content": "Hi"}
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "ANTHROPIC_API_KEY is not configured on the server."
    }


def test_unknown_conversation_returns_404(client: TestClient) -> None:
    assert client.get("/api/chat/conversations/999").status_code == 404
    assert (
        client.post(
            "/api/chat/conversations/999/messages", json={"content": "Hi"}
        ).status_code
        == 404
    )


def test_blank_message_is_rejected(
    client: TestClient, stub_reply: list[list[dict[str, str]]]
) -> None:
    conversation_id = client.post("/api/chat/conversations").json()["id"]

    response = client.post(
        f"/api/chat/conversations/{conversation_id}/messages", json={"content": "   "}
    )

    assert response.status_code == 422
    assert stub_reply == []


def test_tool_calls_are_streamed_as_events_and_not_stored(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def tool_using_stream_reply(history: list[dict[str, str]]) -> Iterator[tuple]:
        yield "text", "Let me check. "
        yield "tool", {"name": "get_issue", "input": {"issue_id": 1}}
        yield "text", "Issue #1 is about login."

    monkeypatch.setattr(chat_routes, "ensure_configured", lambda: None)
    monkeypatch.setattr(chat_routes, "stream_reply", tool_using_stream_reply)
    conversation_id = client.post("/api/chat/conversations").json()["id"]

    events = send(client, conversation_id, "What is issue 1?")

    assert [event for event, _ in events] == ["delta", "tool", "delta", "done"]
    assert events[1][1] == {"name": "get_issue", "input": {"issue_id": 1}}
    stored = events[-1][1]["assistant_message"]["content"]
    assert stored == "Let me check. Issue #1 is about login."
