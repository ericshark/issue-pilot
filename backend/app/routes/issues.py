"""HTTP routes for creating and reading issues."""

import sqlite3
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from app.ai.schemas import TriageResponse
from app.ai.service import TriageUnavailable, triage_issue
from app.database import get_connection
from app.models.issue import Issue, IssueCreate, IssueList

router = APIRouter(prefix="/api/issues", tags=["issues"])


def row_to_issue(row: sqlite3.Row) -> Issue:
    """Convert a SQLite row into the public response model."""

    return Issue.model_validate({key: row[key] for key in row.keys()})


@router.post("", response_model=Issue, status_code=status.HTTP_201_CREATED)
def create_issue(payload: IssueCreate) -> Issue:
    """Validate and persist one issue."""

    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO issues (title, description, created_at)
            VALUES (?, ?, ?)
            """,
            (payload.title, payload.description, created_at),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT id, title, description, created_at
            FROM issues
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise RuntimeError("Inserted issue could not be retrieved")

    return row_to_issue(row)


@router.get("", response_model=IssueList)
def list_issues() -> IssueList:
    """Return every issue, newest first."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, description, created_at
            FROM issues
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

    return IssueList(items=[row_to_issue(row) for row in rows])


@router.get("/{issue_id}", response_model=Issue)
def get_issue(issue_id: Annotated[int, Path(ge=1)]) -> Issue:
    """Return one issue or the contract's not-found response."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, title, description, created_at
            FROM issues
            WHERE id = ?
            """,
            (issue_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    return row_to_issue(row)


@router.post("/{issue_id}/triage", response_model=TriageResponse)
def triage(issue_id: Annotated[int, Path(ge=1)]) -> TriageResponse:
    """Classify one stored issue with Claude without persisting the result."""

    issue = get_issue(issue_id)

    try:
        result, model = triage_issue(issue.title, issue.description)
    except TriageUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return TriageResponse(issue_id=issue.id, model=model, result=result)
