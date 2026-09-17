"""HTTP routes for stored chat conversations with Claude."""

import json
import sqlite3
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status
from fastapi.responses import StreamingResponse

from app.ai.chat import ChatUnavailable, ensure_configured, stream_reply
from app.database import get_connection
from app.models.chat import (
    ChatMessage,
    ChatMessageCreate,
    ChatReply,
    Conversation,
    ConversationDetail,
    ConversationList,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])

UNTITLED = "New chat"
TITLE_LIMIT = 60


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def row_to_conversation(row: sqlite3.Row) -> Conversation:
    return Conversation.model_validate({key: row[key] for key in row.keys()})


def row_to_message(row: sqlite3.Row) -> ChatMessage:
    return ChatMessage.model_validate({key: row[key] for key in row.keys()})


def title_from(content: str) -> str:
    """Derive a list-friendly title from the first user message."""

    first_line = content.strip().splitlines()[0]
    if len(first_line) <= TITLE_LIMIT:
        return first_line
    return first_line[: TITLE_LIMIT - 1].rstrip() + "…"


def fetch_conversation(
    connection: sqlite3.Connection, conversation_id: int
) -> Conversation:
    row = connection.execute(
        "SELECT id, title, created_at FROM conversations WHERE id = ?",
        (conversation_id,),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return row_to_conversation(row)


def fetch_messages(
    connection: sqlite3.Connection, conversation_id: int
) -> list[ChatMessage]:
    rows = connection.execute(
        """
        SELECT id, conversation_id, role, content, created_at
        FROM chat_messages
        WHERE conversation_id = ?
        ORDER BY id ASC
        """,
        (conversation_id,),
    ).fetchall()

    return [row_to_message(row) for row in rows]


def insert_message(
    connection: sqlite3.Connection, conversation_id: int, role: str, content: str
) -> ChatMessage:
    cursor = connection.execute(
        """
        INSERT INTO chat_messages (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (conversation_id, role, content, now_utc()),
    )
    row = connection.execute(
        """
        SELECT id, conversation_id, role, content, created_at
        FROM chat_messages
        WHERE id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()

    if row is None:
        raise RuntimeError("Inserted message could not be retrieved")

    return row_to_message(row)


@router.post(
    "/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED
)
def create_conversation() -> Conversation:
    """Start an empty conversation; it is titled from the first message sent."""

    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO conversations (title, created_at) VALUES (?, ?)",
            (UNTITLED, now_utc()),
        )
        connection.commit()
        assert cursor.lastrowid is not None
        return fetch_conversation(connection, cursor.lastrowid)


@router.get("/conversations", response_model=ConversationList)
def list_conversations() -> ConversationList:
    """Return every conversation, newest first."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, created_at
            FROM conversations
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

    return ConversationList(items=[row_to_conversation(row) for row in rows])


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: Annotated[int, Path(ge=1)]) -> ConversationDetail:
    """Return one conversation with its full history."""

    with get_connection() as connection:
        conversation = fetch_conversation(connection, conversation_id)
        messages = fetch_messages(connection, conversation_id)

    return ConversationDetail(**conversation.model_dump(), messages=messages)


def sse(event: str, data: object) -> str:
    """Format one Server-Sent Event."""

    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/conversations/{conversation_id}/messages")
def send_message(
    conversation_id: Annotated[int, Path(ge=1)], payload: ChatMessageCreate
) -> StreamingResponse:
    """Stream Claude's reply as SSE, then store both turns together.

    Events: ``delta`` with ``{"text"}`` for each chunk and ``tool`` with
    ``{"name", "input"}`` for each issue lookup, then either ``done`` with a
    ``ChatReply`` or ``error`` with ``{"detail"}``. Nothing is written until
    the reply completes, so a failed send can simply be retried.
    """

    with get_connection() as connection:
        conversation = fetch_conversation(connection, conversation_id)
        history = [
            {"role": message.role, "content": message.content}
            for message in fetch_messages(connection, conversation_id)
        ]

    history.append({"role": "user", "content": payload.content})

    # Configuration problems surface as a normal 503 before the stream opens.
    try:
        ensure_configured()
    except ChatUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    def events() -> Iterator[str]:
        parts: list[str] = []

        try:
            for kind, data in stream_reply(history):
                if kind == "text" and isinstance(data, str):
                    parts.append(data)
                    yield sse("delta", {"text": data})
                else:
                    yield sse("tool", data)
        except ChatUnavailable as error:
            yield sse("error", {"detail": str(error)})
            return

        reply = "".join(parts)

        with get_connection() as connection:
            user_message = insert_message(
                connection, conversation_id, "user", payload.content
            )
            assistant_message = insert_message(
                connection, conversation_id, "assistant", reply
            )

            if conversation.title == UNTITLED:
                connection.execute(
                    "UPDATE conversations SET title = ? WHERE id = ?",
                    (title_from(payload.content), conversation_id),
                )

            connection.commit()

        done = ChatReply(user_message=user_message, assistant_message=assistant_message)
        yield sse("done", done.model_dump(mode="json"))

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
