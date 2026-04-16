from flask import Flask, render_template, request, jsonify
import os
import requests


app = Flask(__name__)

WORKFLOW_SERVICE_URL = os.environ.get("WORKFLOW_SERVICE_URL", "http://workflow-service:8001")
DATA_SERVICE_URL = os.environ.get("DATA_SERVICE_URL", "http://data-service:8002")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/result/<submission_id>", methods=["GET"])
def result_page(submission_id):
    return render_template("result.html", submission_id=submission_id)

@app.route("/api/submit", methods=["POST"])
def submit():
    data = request.get_json(force=True)
    try:
        res = requests.post(
            f"{WORKFLOW_SERVICE_URL}/submit",
            json=data,
            timeout=10
        )
        return jsonify(res.json()), res.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Workflow service unavailable"}), 503

@app.route("/api/submission/<submission_id>", methods=["GET"])
def get_submission(submission_id):
    try:
        res = requests.get(
            f"{DATA_SERVICE_URL}/submission/{submission_id}",
            timeout=10
        )
        return jsonify(res.json()), res.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Data service unavailable"}), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)