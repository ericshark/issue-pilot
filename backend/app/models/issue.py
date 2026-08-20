"""Pydantic models for the issue API contract."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer

Title = Annotated[str, StringConstraints(min_length=1, max_length=120)]
Description = Annotated[str, StringConstraints(min_length=1, max_length=5_000)]


class IssueCreate(BaseModel):
    """User-provided fields accepted when creating an issue."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: Title
    description: Description


class Issue(IssueCreate):
    """Complete issue representation returned by the API."""

    id: Annotated[int, Field(ge=1)]
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize UTC timestamps with the contract's trailing Z."""

        return value.isoformat().replace("+00:00", "Z")


class IssueList(BaseModel):
    """Stable wrapper for the issue collection response."""

    items: list[Issue]
