"""Contract tests for the issue endpoints."""

from fastapi.testclient import TestClient


def test_create_issue_trims_and_returns_stored_issue(client: TestClient) -> None:
    response = client.post(
        "/api/issues",
        json={"title": "  Broken login  ", "description": "  Nothing happens.  "},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "title": "Broken login",
        "description": "Nothing happens.",
        "created_at": response.json()["created_at"],
    }
    assert response.json()["created_at"].endswith("Z")


def test_list_issues_returns_newest_first(client: TestClient) -> None:
    first = client.post(
        "/api/issues",
        json={"title": "First", "description": "Created first"},
    ).json()
    second = client.post(
        "/api/issues",
        json={"title": "Second", "description": "Created second"},
    ).json()

    response = client.get("/api/issues")

    assert response.status_code == 200
    assert response.json()["items"] == [second, first]


def test_get_issue_returns_one_issue(client: TestClient) -> None:
    created = client.post(
        "/api/issues",
        json={"title": "One issue", "description": "Full details"},
    ).json()

    response = client.get(f"/api/issues/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_issue_returns_contract_error(client: TestClient) -> None:
    response = client.get("/api/issues/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Issue not found"}


def test_create_rejects_blank_and_unknown_fields(client: TestClient) -> None:
    response = client.post(
        "/api/issues",
        json={"title": "   ", "description": "Details", "status": "open"},
    )

    assert response.status_code == 422
    locations = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", "title") in locations
    assert ("body", "status") in locations
    assert client.get("/api/issues").json() == {"items": []}
