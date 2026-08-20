"""Shared fixtures for isolated API tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Run each test against its own temporary SQLite database."""

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))

    with TestClient(app) as test_client:
        yield test_client
