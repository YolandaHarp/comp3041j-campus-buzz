import json
import os
import requests

DATA_SERVICE_URL = os.environ["DATA_SERVICE_URL"]


def lambda_handler(event, context):
    submission_id = event.get("submission_id")
    result = event.get("result", {})

    if not submission_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "submission_id is required"})
        }

    res = requests.put(
        f"{DATA_SERVICE_URL}/submission/{submission_id}",
        json=result,
        timeout=10
    )

    return {
        "statusCode": res.status_code,
        "body": json.dumps({
            "message": "Result update requested",
            "submission_id": submission_id
        })
    }