"""Environment-backed settings shared by the backend.

The ``.env`` file at the repository root is loaded exactly once, when this
module is first imported. Everything else reads ``os.environ`` at call time so
tests can override values with ``monkeypatch.setenv``.
"""

import os
from functools import lru_cache
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_DATABASE_PATH = PROJECT_ROOT / "backend" / "issuepilot.db"
DEFAULT_TRIAGE_MODEL = "claude-opus-5"
DEFAULT_CHAT_MODEL = "claude-opus-5"
DEFAULT_SMOKE_TEST_MODEL = "claude-haiku-4-5-20251001"


class MissingApiKey(RuntimeError):
    """Raised when a Claude call is attempted without ``ANTHROPIC_API_KEY``."""


def get_database_path() -> Path:
    """Return the configured database path, anchored to the repository root."""

    configured_path = os.getenv("DATABASE_PATH")
    if not configured_path:
        return DEFAULT_DATABASE_PATH

    path = Path(configured_path).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def get_triage_model() -> str:
    return os.getenv("ANTHROPIC_TRIAGE_MODEL") or DEFAULT_TRIAGE_MODEL


def get_chat_model() -> str:
    return os.getenv("ANTHROPIC_CHAT_MODEL") or DEFAULT_CHAT_MODEL


def get_smoke_test_model() -> str:
    return os.getenv("ANTHROPIC_MODEL") or DEFAULT_SMOKE_TEST_MODEL


def require_api_key() -> str:
    """Return the API key or raise :class:`MissingApiKey` with a clear message."""

    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise MissingApiKey("ANTHROPIC_API_KEY is not configured on the server.")
    return key


@lru_cache(maxsize=1)
def get_client() -> Anthropic:
    """Return one shared Anthropic client so its connection pool is reused."""

    return Anthropic(api_key=require_api_key())
