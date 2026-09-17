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

## Triage an issue

`POST /api/issues/{issue_id}/triage`

No request body. Classifies the stored issue with Claude and returns the result
without persisting it. Every call re-runs the classification.

Success: `200 OK` with a `TriageResponse`.

```json
{
  "issue_id": 1,
  "schema_version": "triage_v1",
  "model": "claude-opus-5",
  "result": {
    "type": "bug",
    "priority": "high",
    "component": "auth",
    "summary": "Clicking Log in with valid credentials has no effect.",
    "rationale": "Describes functionality behaving incorrectly, but the report gives no evidence of how many users are affected.",
    "suggested_next_action": "Ask the reporter for browser console errors and whether it reproduces in another browser."
  }
}
```

| Property | Type | Values |
| --- | --- | --- |
| `type` | string | `bug`, `feature_request`, `question`, `task` |
| `priority` | string | `low`, `medium`, `high`, `critical` |
| `component` | string | Short inferred component name, or `unknown` |
| `summary` | string | Concise restatement of the report |
| `rationale` | string | Justification for the classification |
| `suggested_next_action` | string | One concrete next step for a reviewer |

Unknown `issue_id` returns `404` with the not-found response above.

When the classification cannot be produced or validated, the route returns
`503 Service Unavailable` with a `detail` string. The backend never returns a
fabricated or partially valid classification.

```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "detail": "Could not reach the Claude API."
}
```

The result is advisory and is not stored, so it never appears on the `Issue`
object returned by the other routes.

## Chat

Conversations with Claude are stored in two tables, `conversations` and
`chat_messages`, and exposed under `/api/chat`. Timestamps use the same
trailing-`Z` format as issues.

### `Conversation`

```json
{ "id": 1, "title": "New chat", "created_at": "2026-09-16T14:30:00Z" }
```

A conversation starts titled `New chat` and is retitled from the first line of
its first user message, truncated to 60 characters.

### `ChatMessage`

```json
{
  "id": 1,
  "conversation_id": 1,
  "role": "user",
  "content": "What is IssuePilot?",
  "created_at": "2026-09-16T14:30:00Z"
}
```

`role` is `user` or `assistant`.

### Routes

| Method and path | Body | Success |
| --- | --- | --- |
| `POST /api/chat/conversations` | none | `201` with a `Conversation` |
| `GET /api/chat/conversations` | none | `200` with `{ "items": [Conversation] }`, newest first |
| `GET /api/chat/conversations/{id}` | none | `200` with a `Conversation` plus `"messages": [ChatMessage]`, oldest first |
| `POST /api/chat/conversations/{id}/messages` | `{ "content": string }` | `200` `text/event-stream` (see below) |

`content` is trimmed and must be 1-8,000 characters; blank input returns the
standard `422` validation error. Unknown `{id}` returns `404` with
`"Conversation not found"`.

### Sending a message

Sending passes the conversation's full stored history plus the new turn to
Claude and streams the reply back as Server-Sent Events. The assistant can
call read-only tools against the `issues` table while replying; it cannot
create, edit, or delete anything. Each event is
`event: <name>` followed by `data: <JSON>` and a blank line:

| Event | Data | Meaning |
| --- | --- | --- |
| `delta` | `{ "text": string }` | One chunk of the reply, in order. Concatenate them. |
| `tool` | `{ "name": string, "input": object }` | The assistant is reading issues: `list_issues` (`{limit}`), `get_issue` (`{issue_id}`), or `search_issues` (`{query, limit}`). Informational only; tool activity is not stored. |
| `done` | `{ "user_message": ChatMessage, "assistant_message": ChatMessage }` | The reply finished and both turns are stored. Always the last event on success. |
| `error` | `{ "detail": string }` | The reply could not be completed. Discard any `delta` text received; nothing was stored. Always the last event on failure. |

```
event: delta
data: {"text": "Hi there,"}

event: delta
data: {"text": " friend!"}

event: done
data: {"user_message": {...}, "assistant_message": {...}}
```

A missing server API key is reported before the stream opens as a normal `503`
with a `detail` string. Because both turns are written only once the reply is
complete, any failed send leaves the conversation unchanged and can simply be
retried.

## Frontend behavior against the contract

- Submit `IssueCreate` and use the returned `Issue`; do not synthesize IDs or
  timestamps in the browser.
- Disable repeated form submission while the POST request is pending.
- On success, clear the form and refresh or update the issue list.
- Display validation errors near the corresponding field when `loc` identifies
  one; otherwise show a general request error.
- Treat non-2xx responses as failures even if a response body cannot be parsed.

## Not yet contracted

There are no update, delete, status, health, or authentication routes, and no
persisted triage field on `Issue`. Adding one changes this contract and may also
change product scope or architecture, so it requires approval and coordinated
document updates.

