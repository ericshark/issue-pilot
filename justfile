root := justfile_directory()

# Run the backend API with auto-reload.
backend:
    cd {{root}}/backend && .venv/bin/python -m uvicorn app.main:app --reload

# Run the Vite dev server.
frontend:
    cd {{root}}/frontend && npm run dev

# Claude API connectivity smoke test.
ai-client:
    cd {{root}}/backend && .venv/bin/python -m app.ai.client

# Run the triage eval cases (needs ANTHROPIC_API_KEY).
evals:
    cd {{root}}/backend && .venv/bin/python -m scripts.run_evals

# Every check CI runs.
check:
    cd {{root}}/backend && .venv/bin/python -m ruff format --check . && .venv/bin/python -m ruff check . && .venv/bin/python -m pyright && .venv/bin/python -m pytest
    cd {{root}}/frontend && npm run lint && npm run format:check && npm test && npm run build
