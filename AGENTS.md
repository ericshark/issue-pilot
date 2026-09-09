# Coding-agent instructions

This file contains rules for coding agents. Human onboarding belongs in
`README.md`, product requirements belong in `docs/SPEC.md`, architecture
decisions belong in `docs/ARCHITECTURE.md`, and HTTP details belong in
`docs/API_CONTRACT.md`.

## Python quality checks

- Changed Python code must pass Ruff formatting, Ruff linting, and Pyright.
- Resolve diagnostics instead of suppressing them unless a suppression is
  documented and justified.
- Before handing off backend changes, run from `backend/`:

  ```bash
  python -m ruff format --check .
  python -m ruff check .
  python -m pyright
  python -m pytest
  ```
