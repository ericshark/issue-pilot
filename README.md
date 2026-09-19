# IssuePilot

A small tutorial project for learning AI-assisted development: a React
frontend and a FastAPI/SQLite backend where users submit software issues,
plus two Claude-powered features, on-demand **triage** and a **chat**
assistant that can read the issues.

## Stack

React 19 + Vite · FastAPI + Pydantic · SQLite (`sqlite3`) · Anthropic Python
SDK · Pytest, Vitest · GitHub Actions

## Run it

```bash
cp .env.example .env        # add ANTHROPIC_API_KEY for triage and chat

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload     # http://127.0.0.1:8000

cd ../frontend
npm install
npm run dev                                  # http://127.0.0.1:5173
```

Vite proxies `/api` to the backend. With [just](https://github.com/casey/just)
installed: `just backend`, `just frontend`, `just check`, `just evals`.

## Checks

```bash
cd backend && ruff format --check . && ruff check . && pyright && pytest
cd frontend && npm run lint && npm run format:check && npm test && npm run build
```

CI runs the same on every PR.

## How it works

```text
Browser -> React SPA -> /api (JSON, SSE) -> FastAPI -> SQLite
                                                   -> Claude (triage, chat)
```

- `backend/app/routes/` owns HTTP; `models/` are the Pydantic shapes;
  `database.py` opens one SQLite connection per request; `config.py` reads
  `.env`.
- `ai/service.py` is triage: one structured-output call with the prompt in
  `ai/prompts/triage_v1.md`. Results are returned, never stored.
- `ai/chat.py` streams a reply and runs the read-only tools in `ai/tools.py`
  (`list_issues`, `get_issue`, `search_issues`) when the model asks. The
  assistant cannot change issues. Both turns are stored only after the reply
  finishes, so a failed send can be retried.
- Issue text is user data. Both prompts tell the model to treat it as data,
  never instructions.
- `frontend/src/api.js` is the only module that calls the backend; the hash
  (`#/issues`, `#/chat`) is the router.

## API

All routes are JSON under `/api`. Errors are `{"detail": "..."}`; validation
errors use FastAPI's default list shape.

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| `POST` | `/api/issues` | `{title, description}` | `201` Issue |
| `GET` | `/api/issues` | | `{items: Issue[]}` newest first |
| `GET` | `/api/issues/{id}` | | Issue, or `404` |
| `POST` | `/api/issues/{id}/triage` | | `{issue_id, schema_version, model, result}`, or `503` |
| `POST` | `/api/chat/conversations` | | `201` Conversation |
| `GET` | `/api/chat/conversations` | | `{items: Conversation[]}` newest first |
| `GET` | `/api/chat/conversations/{id}` | | Conversation + `messages[]` |
| `POST` | `/api/chat/conversations/{id}/messages` | `{content}` | SSE stream |

Shapes: `Issue {id, title, description, created_at}`,
`Conversation {id, title, created_at}`,
`ChatMessage {id, conversation_id, role, content, created_at}`.
Limits: title 1–120, description 1–5,000, chat content 1–8,000 chars, trimmed.

Triage `result`: `type` ∈ bug | feature_request | question | task,
`priority` ∈ low | medium | high | critical, plus `component`, `summary`,
`rationale`, `suggested_next_action`.

SSE events: `delta {text}` per chunk, `tool {name, input}` per lookup, then
`done {user_message, assistant_message, conversation}` or `error {detail}`
(nothing stored; resend to retry).

## Evals

`evals/triage_cases.json` holds a few labelled reports. `just evals` (or
`cd backend && python -m scripts.run_evals`) runs them through the real
triage prompt and prints pass/fail. Needs an API key; not run in CI.
