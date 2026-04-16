import json
import os
import re
import requests
import boto3

lambda_client = boto3.client("lambda")
DATA_SERVICE_URL = os.environ["DATA_SERVICE_URL"]
RESULT_UPDATE_FUNCTION_NAME = os.environ["RESULT_UPDATE_FUNCTION_NAME"]


def assign_category(text: str) -> str:
    text = text.lower()

    if any(k in text for k in ["career", "internship", "recruitment"]):
        return "OPPORTUNITY"
    if any(k in text for k in ["workshop", "seminar", "lecture"]):
        return "ACADEMIC"
    if any(k in text for k in ["club", "society", "social"]):
        return "SOCIAL"
    return "GENERAL"


def assign_priority(category: str) -> str:
    if category == "OPPORTUNITY":
        return "HIGH"
    if category == "ACADEMIC":
        return "MEDIUM"
    return "NORMAL"


def compute_result(data: dict) -> dict:
    required_fields = ["title", "description", "location", "date", "organizer"]
    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return {
            "status": "INCOMPLETE",
            "category": None,
            "priority": None,
            "note": "Missing required field(s): " + ", ".join(missing)
        }

    date_value = str(data.get("date", "")).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
        category = assign_category(f"{data.get('title', '')} {data.get('description', '')}")
        priority = assign_priority(category)
        return {
            "status": "NEEDS_REVISION",
            "category": category,
            "priority": priority,
            "note": "Date must use YYYY-MM-DD format"
        }

    description = str(data.get("description", ""))
    category = assign_category(f"{data.get('title', '')} {description}")
    priority = assign_priority(category)

    if len(description) < 40:
        return {
            "status": "NEEDS_REVISION",
            "category": category,
            "priority": priority,
            "note": "Description must contain at least 40 characters"
        }

    return {
        "status": "APPROVED",
        "category": category,
        "priority": priority,
        "note": "Submission approved successfully"
    }


def lambda_handler(event, context):
    submission_id = event.get("submission_id")
    if not submission_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "submission_id is required"})
        }

    res = requests.get(f"{DATA_SERVICE_URL}/submission/{submission_id}", timeout=10)
    if res.status_code != 200:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Submission not found"})
        }

    submission = res.json()
    result = compute_result(submission)

    lambda_client.invoke(
        FunctionName=RESULT_UPDATE_FUNCTION_NAME,
        InvocationType="Event",
        Payload=json.dumps({
            "submission_id": submission_id,
            "result": result
        }).encode("utf-8")
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "submission_id": submission_id,
            "result": result
        })
    }