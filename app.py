import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory, abort
from flasgger import Swagger

app = Flask(__name__)

app.config["SWAGGER"] = {
    "title": "Tasks API",
    "uiversion": 3,
    "specs_route": "/docs/",
}
Swagger(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "tasks.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                completed  INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


@app.get("/")
def serve_frontend():
    # index.html должен лежать рядом с app.py
    return send_from_directory(".", "index.html")


@app.get("/tasks")
def get_tasks():
    """
    Get tasks
    ---
    responses:
      200:
        description: List of tasks
        schema:
          type: array
          items:
            type: object
            properties:
              id: { type: integer }
              title: { type: string }
              description: { type: string }
              completed: { type: boolean }
    """
    with get_conn() as conn:
        rows = conn.execute("SELECT id, title, description, completed FROM tasks ORDER BY id DESC").fetchall()
        tasks = [{"id": r["id"], "title": r["title"], "description": r["description"], "completed": bool(r["completed"])} for r in rows]
        return jsonify(tasks), 200


@app.post("/tasks")
def create_task():
    """
    Create task
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [title]
          properties:
            title: { type: string }
    responses:
      201:
        description: Created task
    """
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()   
    if not title:
        return jsonify({"error": "title is required"}), 400

    with get_conn() as conn:
        cur = conn.execute("INSERT INTO tasks(title, description, completed) VALUES(?, ?, ?)", (title, description, 0))
        task_id = cur.lastrowid
        conn.commit()

        row = conn.execute("SELECT id, title, description, completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
        task = {"id": row["id"], "title": row["title"], "description": row["description"], "completed": bool(row["completed"])}
        return jsonify(task), 201


@app.put("/tasks/<int:task_id>")
def update_task(task_id: int):
    """
    Update task
    ---
    parameters:
      - in: path
        name: task_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title: { type: string }
            description: { type: string }
            completed: { type: boolean }
    responses:
      200:
        description: Updated task
      404:
        description: Task not found
    """
    data = request.get_json(silent=True) or {}

    # поддержим и completed, и title (на будущее)
    fields = []
    params = []

    if "completed" in data:
        fields.append("completed = ?")
        params.append(1 if bool(data["completed"]) else 0)
        
    if "description" in data:
        fields.append("description = ?")
        params.append(data["description"])

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        fields.append("title = ?")
        params.append(title)

    if not fields:
        return jsonify({"error": "no fields to update"}), 400

    params.append(task_id)

    with get_conn() as conn:
        cur = conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()

        if cur.rowcount == 0:
            abort(404)

        row = conn.execute("SELECT id, title, description, completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
        task = {"id": row["id"], "title": row["title"], "description": row["description"], "completed": bool(row["completed"])}
        return jsonify(task), 200


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    """
    Delete task
    ---
    parameters:
      - in: path
        name: task_id
        required: true
        type: integer
    responses:
      204:
        description: Deleted
      404:
        description: Task not found
    """
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        if cur.rowcount == 0:
            abort(404)
        return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
