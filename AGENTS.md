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
