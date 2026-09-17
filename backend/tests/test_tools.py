"""Tests for the chat assistant's read-only issue tools."""

import json

from fastapi.testclient import TestClient

from app.ai.tools import execute_tool


def seed(client: TestClient) -> None:
    client.post(
        "/api/issues",
        json={"title": "Login broken", "description": "Button does nothing."},
    )
    client.post(
        "/api/issues",
        json={"title": "Dark mode", "description": "Please add a dark theme."},
    )
    client.post(
        "/api/issues",
        json={"title": "100% CPU", "description": "Fan spins on the login page."},
    )


def test_list_issues_returns_newest_first_with_total(client: TestClient) -> None:
    seed(client)

    content, is_error = execute_tool("list_issues", {"limit": 2})

    assert not is_error
    result = json.loads(content)
    assert result["total"] == 3
    assert [issue["title"] for issue in result["issues"]] == ["100% CPU", "Dark mode"]
    assert result["issues"][0]["excerpt"] == "Fan spins on the login page."


def test_get_issue_returns_full_description(client: TestClient) -> None:
    seed(client)

    content, is_error = execute_tool("get_issue", {"issue_id": 1})

    assert not is_error
    assert json.loads(content)["description"] == "Button does nothing."


def test_get_issue_unknown_id_is_an_error_result(client: TestClient) -> None:
    content, is_error = execute_tool("get_issue", {"issue_id": 42})

    assert is_error
    assert content == "No issue has id 42."


def test_search_matches_title_and_description_case_insensitively(
    client: TestClient,
) -> None:
    seed(client)

    content, is_error = execute_tool("search_issues", {"query": "LOGIN", "limit": 10})

    assert not is_error
    assert [issue["id"] for issue in json.loads(content)["issues"]] == [3, 1]


def test_search_treats_like_wildcards_literally(client: TestClient) -> None:
    seed(client)

    content, _ = execute_tool("search_issues", {"query": "100%", "limit": 10})

    assert [issue["id"] for issue in json.loads(content)["issues"]] == [3]


def test_invalid_input_and_unknown_tool_are_error_results(client: TestClient) -> None:
    content, is_error = execute_tool("list_issues", {"limit": 0})
    assert is_error and content.startswith("Invalid input for list_issues")

    content, is_error = execute_tool("delete_issue", {"issue_id": 1})
    assert is_error and content == "Unknown tool: delete_issue"
