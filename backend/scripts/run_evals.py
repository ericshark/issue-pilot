"""Run the triage prompt against the cases in ``evals/triage_cases.json``.

Run from ``backend/`` with ``python -m scripts.run_evals``. Every case costs one
real Claude call, so this is a manual check, not part of CI. A case passes when
each field in ``expected`` matches (a list means any listed value is fine) and
none of ``forbidden_in_summary`` appears in the summary or rationale.
"""

import json
import sys
from pathlib import Path
from typing import Any

from app.ai.service import TriageUnavailable, triage_issue
from app.config import PROJECT_ROOT

CASES_PATH = PROJECT_ROOT / "evals" / "triage_cases.json"


def matches(expected: Any, actual: str) -> bool:
    return actual in expected if isinstance(expected, list) else actual == expected


def check_case(case: dict[str, Any]) -> list[str]:
    """Return a list of failure reasons; empty means the case passed."""

    try:
        result, _ = triage_issue(case["title"], case["description"])
    except TriageUnavailable as error:
        return [f"triage failed: {error}"]

    actual = result.model_dump()
    failures = [
        f"{field}: expected {expected!r}, got {actual[field]!r}"
        for field, expected in case.get("expected", {}).items()
        if not matches(expected, actual[field])
    ]

    prose = f"{result.summary} {result.rationale}".lower()
    failures += [
        f"summary/rationale contains forbidden text {phrase!r}"
        for phrase in case.get("forbidden_in_summary", [])
        if phrase.lower() in prose
    ]
    return failures


def main(path: Path = CASES_PATH) -> int:
    cases = json.loads(path.read_text(encoding="utf-8"))
    failed = 0

    for case in cases:
        failures = check_case(case)
        status = "PASS" if not failures else "FAIL"
        failed += bool(failures)
        print(f"{status}  {case['name']}")
        for reason in failures:
            print(f"      - {reason}")

    print(f"\n{len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
