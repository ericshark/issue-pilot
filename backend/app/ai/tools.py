"""Read-only tools the chat assistant can call to look at stored issues.

Every tool reads SQLite directly and returns a JSON string for the model.
Inputs are validated with Pydantic before anything runs, so a malformed call
becomes an ``is_error`` result the model can recover from instead of a crash.
Nothing here writes to the database: the assistant is advisory only.
"""

import json
from typing import Annotated, Any

from anthropic.types import ToolParam
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.database import get_connection

EXCERPT_LENGTH = 160
DEFAULT_LIMIT = 10
MAX_LIMIT = 50
LIMIT_DESCRIPTION = (
    f"How many to return, 1 to {MAX_LIMIT}. Use {DEFAULT_LIMIT} unless the user "
    "asks for more."
)


class ListIssuesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: Annotated[int, Field(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT


class GetIssueInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_id: Annotated[int, Field(ge=1)]


class SearchIssuesInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: Annotated[str, Field(min_length=1, max_length=200)]
    limit: Annotated[int, Field(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT


# Strict schemas reject minimum/maximum/minLength/maxLength, so the bounds are
# stated in descriptions and enforced by the Pydantic input models above.
TOOLS: list[ToolParam] = [
    {
        "name": "list_issues",
        "description": (
            "List the most recently submitted issues, newest first. Returns id, "
            "title, created_at, and a short excerpt of each description. Use "
            "get_issue to read a full description."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": LIMIT_DESCRIPTION,
                }
            },
            "required": ["limit"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_issue",
        "description": (
            "Fetch one issue by its numeric id, including the full description. "
            "Returns an error if no issue has that id."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_id": {
                    "type": "integer",
                    "description": "The issue's numeric id.",
                },
            },
            "required": ["issue_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_issues",
        "description": (
            "Find issues whose title or description contains the query text "
            "(case-insensitive substring match). Returns the same summary shape "
            "as list_issues, newest first."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to look for, up to 200 characters.",
                },
                "limit": {
                    "type": "integer",
                    "description": LIMIT_DESCRIPTION,
                },
            },
            "required": ["query", "limit"],
            "additionalProperties": False,
        },
    },
]


def excerpt(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= EXCERPT_LENGTH:
        return collapsed
    return collapsed[:EXCERPT_LENGTH].rstrip() + "…"


def summarize(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "excerpt": excerpt(row["description"]),
    }


def list_issues(params: ListIssuesInput) -> dict[str, Any]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, description, created_at
            FROM issues
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (params.limit,),
        ).fetchall()
        total = connection.execute("SELECT COUNT(*) FROM issues").fetchone()[0]

    return {"total": total, "issues": [summarize(row) for row in rows]}


def get_issue(params: GetIssueInput) -> dict[str, Any]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, title, description, created_at FROM issues WHERE id = ?",
            (params.issue_id,),
        ).fetchone()

    if row is None:
        raise LookupError(f"No issue has id {params.issue_id}.")

    return {key: row[key] for key in row.keys()}


def search_issues(params: SearchIssuesInput) -> dict[str, Any]:
    # LIKE with ESCAPE so a literal % or _ in the query does not become a wildcard.
    escaped = params.query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, description, created_at
            FROM issues
            WHERE title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\'
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (pattern, pattern, params.limit),
        ).fetchall()

    return {"query": params.query, "issues": [summarize(row) for row in rows]}


def execute_tool(name: str, raw_input: object) -> tuple[str, bool]:
    """Run one tool call and return ``(content, is_error)`` for the model."""

    try:
        if name == "list_issues":
            result = list_issues(ListIssuesInput.model_validate(raw_input))
        elif name == "get_issue":
            result = get_issue(GetIssueInput.model_validate(raw_input))
        elif name == "search_issues":
            result = search_issues(SearchIssuesInput.model_validate(raw_input))
        else:
            return f"Unknown tool: {name}", True
    except ValidationError as error:
        return f"Invalid input for {name}: {error.errors()[0]['msg']}", True
    except LookupError as error:
        return str(error), True

    return json.dumps(result), False
