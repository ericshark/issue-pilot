# IssuePilot API contract

## Purpose and scope

This document is the binding interface between the React frontend and FastAPI
backend for the one-day MVP. Product intent belongs in `SPEC.md`; internal
implementation choices belong in `ARCHITECTURE.md`.

All routes are relative to the backend origin and begin with `/api`. Requests
and responses use `Content-Type: application/json`. Property names are
lowercase `snake_case`. Unknown request properties are rejected.

## Shared data shapes

### `IssueCreate`

```json
{
  "title": "Login button does nothing",
  "description": "Clicking Log in after entering valid credentials has no effect."
}
```

| Property | Type | Required | Validation |
| --- | --- | --- | --- |
| `title` | string | yes | Trimmed length 1-120 |
| `description` | string | yes | Trimmed length 1-5,000 |

### `Issue`

```json
{
  "id": 1,
  "title": "Login button does nothing",
  "description": "Clicking Log in after entering valid credentials has no effect.",
  "created_at": "2026-08-06T14:30:00Z"
}
```

| Property | Type | Nullable | Meaning |
| --- | --- | --- | --- |
| `id` | integer | no | Server-generated value, minimum 1 |
| `title` | string | no | Trimmed stored title |
| `description` | string | no | Trimmed stored description |
| `created_at` | string | no | Server-generated UTC ISO 8601 timestamp |

Responses contain exactly these issue properties during the MVP. AI fields are
not included as `null` placeholders.

## Create an issue

`POST /api/issues`

Request body: `IssueCreate`.

Success: `201 Created` with the newly stored `Issue` as the response body.

Example:

```http
POST /api/issues
Content-Type: application/json

{
  "title": "Login button does nothing",
  "description": "Clicking Log in after entering valid credentials has no effect."
}
```

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 1,
  "title": "Login button does nothing",
  "description": "Clicking Log in after entering valid credentials has no effect.",
  "created_at": "2026-08-06T14:30:00Z"
}
```

## List issues

`GET /api/issues`

Success: `200 OK` with an `IssueList` object. Items are ordered by
`created_at` descending, with `id` descending as the deterministic tie-breaker.

```json
{
  "items": [
    {
      "id": 1,
      "title": "Login button does nothing",
      "description": "Clicking Log in after entering valid credentials has no effect.",
      "created_at": "2026-08-06T14:30:00Z"
    }
  ]
}
```

When no issues exist, the response is `{ "items": [] }`. Pagination metadata
and query parameters are not part of the MVP.

## Get one issue

`GET /api/issues/{issue_id}`

`issue_id` must be a positive integer.

Success: `200 OK` with one `Issue`.

If no stored issue has that ID:

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Issue not found"
}
```

## Validation errors

Malformed JSON, missing fields, unknown fields, invalid path values, and values
outside the documented constraints return `422 Unprocessable Entity` using
FastAPI's standard validation response shape:

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "type": "string_too_short"
    }
  ]
}
```

The exact `msg` and `type` text may vary with the installed Pydantic version.
Frontend logic must rely on the status code and `loc`, not exact English error
wording.

## Server errors

Unexpected backend or database failures return:

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "detail": "Internal server error"
}
```

Internal exception and database details must not appear in the response.

## Frontend behavior against the contract

- Submit `IssueCreate` and use the returned `Issue`; do not synthesize IDs or
  timestamps in the browser.
- Disable repeated form submission while the POST request is pending.
- On success, clear the form and refresh or update the issue list.
- Display validation errors near the corresponding field when `loc` identifies
  one; otherwise show a general request error.
- Treat non-2xx responses as failures even if a response body cannot be parsed.

## Not yet contracted

There are no update, delete, status, health, authentication, or AI triage routes
in this milestone. Adding one changes this contract and may also change product
scope or architecture, so it requires approval and coordinated document updates.

