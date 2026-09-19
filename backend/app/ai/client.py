"""Standalone Claude API connectivity smoke test.

Run from ``backend/`` with ``python -m app.ai.client``. This module is not
connected to the FastAPI application or the issue-triage workflow.
"""

from anthropic import APIError

from app.config import MissingApiKey, get_client, get_smoke_test_model

TEST_PROMPT = "tell me the first 20 amendments"


def make_test_request() -> str:
    """Send one small request and return the model's text response."""

    try:
        client = get_client()
    except MissingApiKey as error:
        raise RuntimeError(f"{error} Add it to the repository's .env file.") from error

    message = client.messages.create(
        model=get_smoke_test_model(),
        max_tokens=300,
        messages=[{"role": "user", "content": TEST_PROMPT}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")

    if not text:
        raise RuntimeError("Claude returned no text content.")

    return text


def main() -> None:
    """Run the smoke test and print a concise result."""

    try:
        print(make_test_request())
    except (APIError, RuntimeError) as error:
        raise SystemExit(f"Claude API test failed: {error}") from error


if __name__ == "__main__":
    main()
