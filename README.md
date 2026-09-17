# IssuePilot

IssuePilot is a hands-on tutorial project for learning professional,
AI-assisted software development. The finished product will be a small React
and FastAPI application where users submit software issues and review them. A
later milestone will add Claude-powered issue triage.

The issue-submission MVP runs, Claude-powered triage is live as an advisory,
on-demand route that does not store its results, and a **Chat** page holds
stored conversations with Claude. A standalone API connectivity smoke test is
also available for learning the Anthropic Python SDK.

## Planned technology

- React with Vite and JavaScript
- FastAPI and Pydantic
- SQLite, accessed with Python's standard `sqlite3` module for the MVP
- Pytest
- Anthropic Python SDK for Claude
- GitHub Actions in a later milestone

## Document map

Each file has one audience and one job:

- `README.md` helps humans understand the repository and learning sequence.
- `AGENTS.md` gives coding agents repository-specific operating rules.
- `.env.example` documents configuration names without holding secrets.
- `.gitignore` keeps local and generated files out of version control.
- `docs/SPEC.md` defines product scope, user behavior, and acceptance criteria.
- `docs/ARCHITECTURE.md` records system boundaries and technical decisions.
- `docs/API_CONTRACT.md` is the exact agreement between frontend and backend.
- `docs/AI_BEHAVIOR.md` defines the classifier's responsibilities and safety
  boundaries.
- `docs/HOW_IT_WORKS.md` explains every file and follows a request through the
  frontend, API, and database.

## Recommended reading order

Start with the product scope in `docs/SPEC.md`, then read
`docs/ARCHITECTURE.md` to understand the system, and finally read
`docs/API_CONTRACT.md` to see the data crossing the frontend/backend boundary.
Read `docs/AI_BEHAVIOR.md` before changing triage behavior.

## Tutorial milestones

1. Agree on documentation and interfaces. **Complete.**
2. Build and test the FastAPI/SQLite issue API. **Current milestone.**
3. Build the React interface against the agreed API. **Current milestone.**
4. Add structured AI triage and evaluation cases. **Triage complete; evaluation
   cases still to do.**
5. Expand the basic CI workflow as additional checks become useful.

Architecture changes require the repository owner's approval before they are
implemented or recorded as decisions.

## Run the backend

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive API documentation
is at `http://127.0.0.1:8000/docs`.

## Run the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite forwards `/api` requests to the backend.

## Run the checks

```bash
cd backend
python -m ruff format --check .
python -m ruff check .
python -m pyright
python -m pytest

cd ../frontend
npm run build
```

## Test the Claude API connection

Add `ANTHROPIC_API_KEY` to the repository's ignored `.env` file, install the
backend dependencies, and run:

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m app.ai.client
```

This sends one short Claude Messages API request and prints the returned text. It is
not connected to FastAPI, stored issues, or the triage feature. Override
the default model by setting `ANTHROPIC_MODEL` in `.env`.

## Run AI triage

Triage needs `ANTHROPIC_API_KEY` in the repository's ignored `.env` file. With
the backend running, open any issue in the UI and choose **Run AI triage**, or
call the route directly:

```bash
curl -X POST http://127.0.0.1:8000/api/issues/1/triage
```

Claude classifies the report's type, priority, and component, then suggests a
next step. The result is advisory, is never written to the database, and is
re-generated on each request. Set `ANTHROPIC_TRIAGE_MODEL` in `.env` to override
the default model.

## Chat

The **Chat** button in the top bar opens a conversation with Claude that can
read the tracker's issues: ask it what has been reported, to find issues about
a topic, or to summarize one by number, and it looks them up with read-only
tools (`backend/app/ai/tools.py`). It cannot change issues. Lookups are shown
as chips in the reply. Conversations and their messages are stored in SQLite
and listed in the sidebar, so any of them can be resumed. Set `ANTHROPIC_CHAT_MODEL` in `.env`
to override the default model.
