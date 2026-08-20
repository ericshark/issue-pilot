---
name: verify-change
description: Verify IssuePilot changes before handoff by selecting and running the relevant backend, frontend, documentation, and skill checks. Use after modifying IssuePilot files, before reporting implementation work complete, or when asked whether the repository is healthy.
---

# Verify Change

Verify the smallest relevant surface, then report exact commands and results.

## Workflow

1. Read `AGENTS.md` and the documents governing the changed behavior.
2. Inspect the working tree and identify frontend, backend, documentation,
   workflow, and skill changes.
3. Run backend checks when `backend/` or the API contract changed, with
   `backend/` as the working directory:
   - `python -m ruff format --check .`
   - `python -m ruff check .`
   - `python -m pyright`
   - `python -m pytest`
4. Run frontend checks when `frontend/` or the API contract changed:
   run `npm run build` with `frontend/` as the working directory.
5. Check documentation references and cross-file agreement when `docs/`,
   `README.md`, or `AGENTS.md` changed.
6. Validate this skill when its files changed by running the skill creator's
   `quick_validate.py` against `.agents/skills/verify-change`.
7. Review `git diff --check` and the final diff for secrets, generated files,
   accidental scope expansion, and API mismatches.
8. Report passed checks, failed checks, skipped checks with reasons, and any
   remaining risks. Never claim a check ran when it did not.

If a required dependency is unavailable, report the exact blocker and continue
with every other safe check.
