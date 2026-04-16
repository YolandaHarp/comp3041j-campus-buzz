from flask import Flask, request, jsonify
import os
import requests
import boto3
import json

# Initialize Flask application
app = Flask(__name__)

# Get Data Service URL from environment variables or use default
DATA_SERVICE_URL = os.environ.get("DATA_SERVICE_URL", "http://data-service:8002")
# Get AWS region from environment variables or use default
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-1")
# Get Lambda function name from environment variables or use default
SUBMISSION_EVENT_FUNCTION = os.environ.get(
    "SUBMISSION_EVENT_FUNCTION",
    "campus-buzz-submission-event"
)

# Create boto3 Lambda client
lambda_client = boto3.client("lambda", region_name=AWS_REGION)


@app.route("/health", methods=["GET"])
def health():
    # Health check endpoint
    return jsonify({"status": "ok"}), 200


@app.route("/submit", methods=["POST"])
def submit():
    # Get JSON data from the request
    data = request.get_json(force=True)
    required_keys = ["title", "description", "location", "date", "organizer"]
    # Ensure all required keys are present, set as None if missing
    for key in required_keys:
        if key not in data:
            data[key] = None

    # Step 1: Create initial submission record in Data Service
    create_res = requests.post(
        f"{DATA_SERVICE_URL}/submission",
        json=data,
        timeout=10,
    )
    if create_res.status_code != 201:
        # If creation fails, return error
        return jsonify({"error": "Failed to create submission"}), 500

    result = create_res.json()
    submission_id = result["submission_id"]

    # Step 2: Invoke AWS Lambda function for further processing
    payload = {"submission_id": submission_id}
    lambda_client.invoke(
        FunctionName=SUBMISSION_EVENT_FUNCTION,
        InvocationType="Event",
        Payload=json.dumps(payload).encode("utf-8"),
    )

    # Return a response with the submission ID and status
    return jsonify({
        "submission_id": submission_id,
        "status": "PENDING"
    }), 202


if __name__ == "__main__":
    # Run the Flask app on 0.0.0.0:8001
    app.run(host="0.0.0.0", port=8001)