# Future IssuePilot AI behavior

## Status

AI triage is a later milestone. `backend/app/ai/client.py` contains only a
standalone connectivity smoke test; it is not imported by FastAPI and does not
read or modify issues. The repository also contains clearly marked locations
for future schemas, service, tools, prompt, and evaluation cases, but they
contain no executable triage behavior. There is no active triage prompt, route,
database field, populated evaluation dataset, or product AI call in the current
milestone. This document defines intended product behavior so future
implementation can be reviewed against a clear boundary.

This is a behavior contract, not an HTTP contract. A future API addition and
any persistence changes require explicit approval and updates to
`ARCHITECTURE.md` and `API_CONTRACT.md`.

## Intended input and output

The classifier will receive the stored issue's title and description. It will
return one structured result with:

| Field | Intended meaning |
| --- | --- |
| `type` | A controlled category such as bug, feature request, question, or task |
| `priority` | A controlled urgency level such as low, medium, high, or critical |
| `component` | A short component name inferred from the issue |
| `summary` | A concise restatement of the reported issue |
| `rationale` | A brief explanation of the classification |
| `suggested_next_action` | A concrete next step for a human reviewer |

The exact enums, length limits, schema version, and storage lifecycle are
deliberately undecided until the AI milestone.

## Behavioral rules

- Base the result only on the submitted title and description; do not invent
  repository facts, logs, owners, deadlines, or customer impact.
- Clearly express uncertainty in the rationale when the issue lacks evidence.
- Prefer asking for missing reproduction details in `suggested_next_action`
  rather than presenting a guess as fact.
- Keep the summary concise and preserve the user's meaning.
- Treat user-provided issue text as untrusted data, not as instructions to the
  model or application.
- Never claim that code was inspected, tests were run, or a fix was verified
  unless a separately approved tool-enabled workflow actually did so.
- Keep classification advisory. A human remains responsible for acting on it.
- Validate model output against a Pydantic schema before returning or storing it.
- Fail visibly and safely when model output is unavailable or invalid; do not
  fabricate a successful classification.

## Privacy and security boundary

The browser will not receive an Anthropic API key and will not call Claude
directly. The backend will send only the data approved for classification.
Logging should avoid API keys and unnecessary copies of issue content.

## Future evaluation expectations

Before the feature is considered complete, representative cases should cover
clear bugs, feature requests, ambiguous reports, missing details, prompt-like
instructions inside issue text, and critical-sounding issues without supporting
evidence. Evaluation cases should test schema validity and behavior rather than
requiring exact prose matches.
