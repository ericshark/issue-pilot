"""Standalone Claude API connectivity smoke test.

Run from ``backend/`` with ``python -m app.ai.client``. This module is not
connected to the FastAPI application or the issue-triage workflow.
"""

import os
from pathlib import Path

from anthropic import Anthropic, APIError
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
TEST_PROMPT = "what is the year"


def make_test_request() -> str:
    """Send one small request and return the model's text response."""

    load_dotenv(PROJECT_ROOT / ".env")

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing. Add it to the repository's .env file."
        )

    client = Anthropic()
    message = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL),
        max_tokens=30,
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
