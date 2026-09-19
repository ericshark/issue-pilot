# Agent rules

- Backend changes must pass, from `backend/`: `ruff format --check .`,
  `ruff check .`, `pyright`, `pytest`.
- Frontend changes must pass, from `frontend/`: `npm run lint`,
  `npm run format:check`, `npm test`, `npm run build`.
- Fix diagnostics rather than suppressing them.
- Do not commit or push unless asked.
