"""Pydantic models for the chat API contract."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer

Role = Literal["user", "assistant"]
MessageContent = Annotated[str, StringConstraints(min_length=1, max_length=8_000)]


def serialize_utc(value: datetime) -> str:
    """Serialize UTC timestamps with the contract's trailing Z."""

    return value.isoformat().replace("+00:00", "Z")


class ChatMessageCreate(BaseModel):
    """One user turn submitted to a conversation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    content: MessageContent


class ChatMessage(BaseModel):
    """One stored turn, from either side."""

    id: Annotated[int, Field(ge=1)]
    conversation_id: Annotated[int, Field(ge=1)]
    role: Role
    content: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return serialize_utc(value)


class Conversation(BaseModel):
    """Conversation summary without its messages."""

    id: Annotated[int, Field(ge=1)]
    title: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return serialize_utc(value)


class ConversationDetail(Conversation):
    """Conversation with its full message history, oldest first."""

    messages: list[ChatMessage]


class ConversationList(BaseModel):
    """Stable wrapper for the conversation collection response."""

    items: list[Conversation]


class ChatReply(BaseModel):
    """Both turns stored by one send: the user's and the assistant's."""

    user_message: ChatMessage
    assistant_message: ChatMessage
