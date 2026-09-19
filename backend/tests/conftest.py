"""Shared fixtures for isolated API tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_client
from app.main import app


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Start every test without an API key and without a cached client."""

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    get_client.cache_clear()
    yield
    get_client.cache_clear()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Run each test against its own temporary SQLite database."""

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))

    with TestClient(app) as test_client:
        yield test_client
