from flask import Flask, request, jsonify
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)
DB_PATH = "/data/submissions.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            location TEXT,
            date TEXT,
            organizer TEXT,
            status TEXT,
            category TEXT,
            priority TEXT,
            note TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/submission", methods=["POST"])
def create_submission():
    data = request.get_json(force=True)
    submission_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    conn.execute("""
        INSERT INTO submissions (
            id, title, description, location, date, organizer,
            status, category, priority, note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        submission_id,
        data.get("title"),
        data.get("description"),
        data.get("location"),
        data.get("date"),
        data.get("organizer"),
        "PENDING",
        None,
        None,
        "Processing started",
        now
    ))
    conn.commit()
    conn.close()
    return jsonify({
        "submission_id": submission_id,
        "status": "PENDING"
    }), 201

@app.route("/submission/<submission_id>", methods=["GET"])
def get_submission(submission_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM submissions WHERE id = ?",
        (submission_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "Submission not found"}), 404
    return jsonify(dict(row)), 200

@app.route("/submission/<submission_id>", methods=["PUT"])
def update_submission(submission_id):
    data = request.get_json(force=True)
    allowed_fields = ["status", "category", "priority", "note"]
    updates = []
    values = []
    for field in allowed_fields:
        if field in data:
            updates.append(f"{field} = ?")
            values.append(data[field])
    if not updates:
        return jsonify({"error": "No update fields provided"}), 400
    values.append(submission_id)
    conn = get_conn()
    cur = conn.execute(
        f"UPDATE submissions SET {', '.join(updates)} WHERE id = ?",
        values
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return jsonify({"error": "Submission not found"}), 404
    return jsonify({"message": "Submission updated"}), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8002)