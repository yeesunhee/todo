import os
from datetime import datetime

import psycopg
from flask import Flask, g, jsonify, render_template, request
from psycopg.rows import dict_row

app = Flask(__name__)


def get_database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL 환경 변수가 설정되어 있지 않습니다.")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def get_db():
    if "db" not in g:
        g.db = psycopg.connect(get_database_url(), row_factory=dict_row)
    return g.db


@app.teardown_appcontext
def close_db(_exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with psycopg.connect(get_database_url()) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT LOCALTIMESTAMP
            )
            """
        )
        db.commit()


def row_to_todo(row):
    created_at = row["created_at"]
    if isinstance(created_at, datetime):
        created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
    return {
        "id": row["id"],
        "title": row["title"],
        "completed": bool(row["completed"]),
        "created_at": created_at,
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/todos")
def list_todos():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, title, completed, created_at
        FROM todos
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()
    return jsonify([row_to_todo(row) for row in rows])


@app.post("/api/todos")
def create_todo():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "할 일을 입력해 주세요."}), 400

    db = get_db()
    row = db.execute(
        """
        INSERT INTO todos (title)
        VALUES (%s)
        RETURNING id, title, completed, created_at
        """,
        (title,),
    ).fetchone()
    db.commit()
    return jsonify(row_to_todo(row)), 201


@app.patch("/api/todos/<int:todo_id>")
def update_todo(todo_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute(
        """
        SELECT id, title, completed, created_at
        FROM todos
        WHERE id = %s
        """,
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
        completed = bool(data.get("completed"))

    updated = db.execute(
        """
        UPDATE todos
        SET title = %s, completed = %s
        WHERE id = %s
        RETURNING id, title, completed, created_at
        """,
        (title, completed, todo_id),
    ).fetchone()
    db.commit()
    return jsonify(row_to_todo(updated))


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    db = get_db()
    cursor = db.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({"error": "할 일을 찾을 수 없습니다."}), 404
    return ("", 204)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
