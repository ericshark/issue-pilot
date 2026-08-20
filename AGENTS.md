# Coding-agent instructions

This file contains rules for coding agents. Human onboarding belongs in
`README.md`, product requirements belong in `docs/SPEC.md`, architecture
decisions belong in `docs/ARCHITECTURE.md`, and HTTP details belong in
`docs/API_CONTRACT.md`.

## Required context

Before changing the project, read:

1. `README.md`
2. `docs/SPEC.md`
3. `docs/ARCHITECTURE.md`
4. `docs/API_CONTRACT.md`
5. `docs/AI_BEHAVIOR.md` when working on AI behavior

## Working rules

- Keep the project small enough for its current tutorial milestone.
- Do not change the planned architecture without the repository owner's
  explicit approval.
- Do not invent product behavior. If the documents do not settle a choice that
  affects users or architecture, ask before implementing it.
- Treat `docs/API_CONTRACT.md` as the shared source of truth for frontend and
  backend request and response shapes.
- Update the relevant document in the same change when approved behavior,
  architecture, or API details change.
- Never commit secrets, local databases, virtual environments, dependencies, or
  generated build output.
- Keep AI output advisory and structured. Do not let generated text directly
  mutate stored issue data without an explicit product decision.
- Add the smallest useful tests with implementation work and report what was
  verified.

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

## Current milestone limits

This milestone implements the issue-submission MVP. Keep the issue API and UI
inside the approved contract. `backend/app/ai/client.py` is approved only as a
standalone Claude connectivity smoke test. The remaining AI files, prompt, and
`evals/` are teaching placeholders: do not connect AI to FastAPI, implement
triage, or persist AI results without explicit approval. Do not add MCP
configuration or worktrees.

Before handing off a change, use the repository-local `verify-change` skill at
`.agents/skills/verify-change/SKILL.md`.
