import json
import boto3
import os

lambda_client = boto3.client("lambda")
PROCESSING_FUNCTION_NAME = os.environ["PROCESSING_FUNCTION_NAME"]


def lambda_handler(event, context):
    submission_id = event.get("submission_id")

    if not submission_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "submission_id is required"})
        }

    lambda_client.invoke(
        FunctionName=PROCESSING_FUNCTION_NAME,
        InvocationType="Event",
        Payload=json.dumps({"submission_id": submission_id}).encode("utf-8")
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Processing started",
            "submission_id": submission_id
        })
    }