import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request

DATABASE = Path(__file__).parent / "todos.db"

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    db.commit()
    db.close()


def row_to_todo(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/todos")
def list_todos():
    db = get_db()
    rows = db.execute(
        "SELECT id, title, completed, created_at FROM todos ORDER BY created_at DESC, id DESC"
    ).fetchall()
    return jsonify([row_to_todo(row) for row in rows])


@app.post("/api/todos")
def create_todo():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "할 일을 입력해 주세요."}), 400

    db = get_db()
    cursor = db.execute("INSERT INTO todos (title) VALUES (?)", (title,))
    db.commit()
    row = db.execute(
        "SELECT id, title, completed, created_at FROM todos WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return jsonify(row_to_todo(row)), 201


@app.patch("/api/todos/<int:todo_id>")
def update_todo(todo_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute(
        "SELECT id, title, completed, created_at FROM todos WHERE id = ?",
        (todo_id,),
    ).fetchone()
    if row is None:
        return jsonify({"error": "할 일을 찾을 수 없습니다."}), 404

    title = row["title"]
    completed = row["completed"]

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "할 일을 입력해 주세요."}), 400

    if "completed" in data:
        completed = 1 if data.get("completed") else 0

    db.execute(
        "UPDATE todos SET title = ?, completed = ? WHERE id = ?",
        (title, completed, todo_id),
    )
    db.commit()
    updated = db.execute(
        "SELECT id, title, completed, created_at FROM todos WHERE id = ?",
        (todo_id,),
    ).fetchone()
    return jsonify(row_to_todo(updated))


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    db = get_db()
    cursor = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({"error": "할 일을 찾을 수 없습니다."}), 404
    return ("", 204)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
