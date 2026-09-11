"""Validated schemas for AI issue triage.

The controlled vocabularies here are the enums promised in
``docs/AI_BEHAVIOR.md``. ``Literal`` is used rather than ``enum.Enum`` so the
generated JSON Schema inlines the allowed values instead of emitting ``$ref``
indirection, which the structured-output API does not accept.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

IssueType = Literal["bug", "feature_request", "question", "task"]
Priority = Literal["low", "medium", "high", "critical"]

TRIAGE_SCHEMA_VERSION = "triage_v1"


class TriageResult(BaseModel):
    """One advisory classification, validated before it leaves the backend."""

    model_config = ConfigDict(extra="forbid")

    type: IssueType = Field(description="The category that best fits the report.")
    priority: Priority = Field(
        description=(
            "Urgency justified by the report alone. Use critical only for "
            "described data loss, security exposure, or total outage."
        )
    )
    component: str = Field(
        description=(
            "Short lowercase component name inferred from the text, such as "
            "'auth' or 'billing'. Use 'unknown' when the text does not say."
        )
    )
    summary: str = Field(
        description=(
            "One or two sentences restating the issue in the reporter's meaning."
        )
    )
    rationale: str = Field(
        description=(
            "Brief justification for the classification. State the uncertainty "
            "plainly when the report lacks evidence."
        )
    )
    suggested_next_action: str = Field(
        description=(
            "One concrete next step for a human reviewer. Ask for the missing "
            "reproduction details when the report is incomplete."
        )
    )


class TriageResponse(BaseModel):
    """Envelope returned by the triage route."""

    issue_id: int
    schema_version: str = TRIAGE_SCHEMA_VERSION
    model: str
    result: TriageResult
