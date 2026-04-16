import time
import sys
from typing import Any, Dict, Optional

import requests


BASE_HOST = "http://3.26.200.234"
SUBMIT_URL = f"{BASE_HOST}:8001/submit"
DATA_URL = f"{BASE_HOST}:8002/submission"


class TestFailure(Exception):
    pass


def submit_event(payload: Dict[str, Any]) -> str:
    response = requests.post(
        SUBMIT_URL,
        json=payload,
        timeout=15,
        headers={"Content-Type": "application/json"},
    )

    print(f"[INFO] Submit response: status={response.status_code}, body={response.text}")

    if response.status_code not in (200, 201, 202):
        raise TestFailure(
            f"Submit failed: status={response.status_code}, body={response.text}"
        )

    data = response.json()

    if "submission_id" not in data:
        raise TestFailure(f"No submission_id returned: {data}")

    return data["submission_id"]


def get_submission(submission_id: str) -> Dict[str, Any]:
    response = requests.get(f"{DATA_URL}/{submission_id}", timeout=15)

    if response.status_code != 200:
        raise TestFailure(
            f"Get submission failed: status={response.status_code}, body={response.text}"
        )

    return response.json()


def wait_for_final_result(
    submission_id: str,
    timeout_seconds: int = 20,
    interval_seconds: float = 1.0,
) -> Dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_data: Optional[Dict[str, Any]] = None

    while time.time() < deadline:
        data = get_submission(submission_id)
        last_data = data
        status = data.get("status")
        print(f"[INFO] Polling {submission_id}: status={status}")

        if status and status != "PENDING":
            return data

        time.sleep(interval_seconds)

    raise TestFailure(
        f"Timed out waiting for final result. Last response: {last_data}"
    )


def assert_equal(actual: Any, expected: Any, field_name: str) -> None:
    if actual != expected:
        raise TestFailure(
            f"{field_name} mismatch: expected={expected!r}, actual={actual!r}"
        )


def assert_non_empty(value: Any, field_name: str) -> None:
    if value is None:
        raise TestFailure(f"{field_name} is None")
    if isinstance(value, str) and not value.strip():
        raise TestFailure(f"{field_name} is empty")


def run_case(
    name: str,
    payload: Dict[str, Any],
    expected_status: str,
    expected_category: Optional[str] = None,
    expected_priority: Optional[str] = None,
) -> None:
    print(f"\n===== Running test: {name} =====")
    submission_id = submit_event(payload)
    print(f"[INFO] submission_id = {submission_id}")

    result = wait_for_final_result(submission_id)
    print(f"[INFO] Final result = {result}")

    # 结果必须包含题目要求的字段
    assert_non_empty(result.get("status"), "status")
    assert_non_empty(result.get("note"), "note")

    assert_equal(result.get("status"), expected_status, "status")

    if expected_category is not None:
        assert_equal(result.get("category"), expected_category, "category")

    if expected_priority is not None:
        assert_equal(result.get("priority"), expected_priority, "priority")

    print(f"[PASS] {name}")


def main() -> int:
    try:
        # 1) APPROVED + ACADEMIC
        run_case(
            name="APPROVED academic",
            payload={
                "title": "Workshop on AI",
                "description": "This workshop introduces practical AI tools and project ideas for all students joining the event.",
                "location": "Room A",
                "date": "2026-04-20",
                "organizer": "CS Club",
            },
            expected_status="APPROVED",
            expected_category="ACADEMIC",
            expected_priority="MEDIUM",
        )

        # 2) APPROVED + OPPORTUNITY
        run_case(
            name="APPROVED opportunity",
            payload={
                "title": "Career Fair Recruitment",
                "description": "This event provides internship and recruitment opportunities for students from many different companies.",
                "location": "Main Hall",
                "date": "2026-05-10",
                "organizer": "Career Office",
            },
            expected_status="APPROVED",
            expected_category="OPPORTUNITY",
            expected_priority="HIGH",
        )

        # 3) APPROVED + SOCIAL
        run_case(
            name="APPROVED social",
            payload={
                "title": "Society social evening",
                "description": "The student society is hosting a large social evening for new members to meet and connect on campus.",
                "location": "Student Center",
                "date": "2026-05-18",
                "organizer": "Student Society",
            },
            expected_status="APPROVED",
            expected_category="SOCIAL",
            expected_priority="NORMAL",
        )

        # 4) APPROVED + GENERAL
        run_case(
            name="APPROVED general",
            payload={
                "title": "Campus notice board update",
                "description": "This event shares general campus information and provides useful updates for students during the semester.",
                "location": "Library Entrance",
                "date": "2026-05-22",
                "organizer": "Campus Office",
            },
            expected_status="APPROVED",
            expected_category="GENERAL",
            expected_priority="NORMAL",
        )

        # 5) NEEDS_REVISION - invalid date
        run_case(
            name="NEEDS_REVISION invalid date",
            payload={
                "title": "Workshop on AI",
                "description": "This workshop introduces practical AI tools and project ideas for all students joining the event.",
                "location": "Room A",
                "date": "20-04-2026",
                "organizer": "CS Club",
            },
            expected_status="NEEDS_REVISION",
            expected_category="ACADEMIC",
            expected_priority="MEDIUM",
        )

        # 6) NEEDS_REVISION - short description
        run_case(
            name="NEEDS_REVISION short description",
            payload={
                "title": "Workshop on AI",
                "description": "Too short for approval.",
                "location": "Room A",
                "date": "2026-04-20",
                "organizer": "CS Club",
            },
            expected_status="NEEDS_REVISION",
            expected_category="ACADEMIC",
            expected_priority="MEDIUM",
        )

        # 7) INCOMPLETE - missing required field
        run_case(
            name="INCOMPLETE missing title",
            payload={
                "title": "",
                "description": "This description is long enough but the title is missing, so the final status should be incomplete.",
                "location": "Room A",
                "date": "2026-04-20",
                "organizer": "CS Club",
            },
            expected_status="INCOMPLETE",
        )

        # 8) precedence: OPPORTUNITY > ACADEMIC
        run_case(
            name="Precedence opportunity over academic",
            payload={
                "title": "Internship workshop",
                "description": "This workshop also contains internship information for students and should be classified as opportunity first.",
                "location": "Engineering Building",
                "date": "2026-06-01",
                "organizer": "Career Team",
            },
            expected_status="APPROVED",
            expected_category="OPPORTUNITY",
            expected_priority="HIGH",
        )

        # 9) precedence: ACADEMIC > SOCIAL
        run_case(
            name="Precedence academic over social",
            payload={
                "title": "Seminar and society introduction",
                "description": "This seminar includes a society introduction session but should still be classified as academic first.",
                "location": "Lecture Hall 2",
                "date": "2026-06-03",
                "organizer": "Faculty Office",
            },
            expected_status="APPROVED",
            expected_category="ACADEMIC",
            expected_priority="MEDIUM",
        )

        print("\n✅ All assignment-aligned tests passed.")
        return 0

    except TestFailure as exc:
        print(f"\n❌ Test failed: {exc}")
        return 1
    except requests.RequestException as exc:
        print(f"\n❌ Network/request error: {exc}")
        return 1
    except Exception as exc:
        print(f"\n❌ Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())