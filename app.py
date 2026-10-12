"""Student Management System - Flask REST API with SQLite storage."""
import os
import re
import sqlite3

from flask import Flask, g, jsonify, request

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")

app = Flask(__name__)
app.config["DATABASE"] = DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no    TEXT    NOT NULL UNIQUE,
    name       TEXT    NOT NULL,
    class_name TEXT    NOT NULL,
    marks      REAL    NOT NULL CHECK (marks BETWEEN 0 AND 100),
    contact    TEXT    NOT NULL,
    email      TEXT,
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);
"""


# ---------- database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.executescript(SCHEMA)


def row_to_dict(row):
    d = dict(row)
    d["class"] = d.pop("class_name")
    return d


# ---------- CORS (frontend runs on a different port via Node tooling) ----------
@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return resp


@app.route("/api/<path:_p>", methods=["OPTIONS"])
def preflight(_p):
    return "", 204


# ---------- validation ----------
def validate(data):
    """Return (clean_dict, errors_dict). Server-side validation."""
    errors, clean = {}, {}
    if not isinstance(data, dict):
        return None, {"body": "Request body must be a JSON object."}

    roll = str(data.get("roll_no", "")).strip()
    if not roll:
        errors["roll_no"] = "Roll number is required."
    elif not re.fullmatch(r"[A-Za-z0-9\-/]{1,20}", roll):
        errors["roll_no"] = "Use letters, digits, '-' or '/' (max 20)."
    clean["roll_no"] = roll

    name = str(data.get("name", "")).strip()
    if not name:
        errors["name"] = "Name is required."
    elif not re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{0,59}", name):
        errors["name"] = "Name must contain letters only (max 60 characters)."
    clean["name"] = name

    cls = str(data.get("class", "")).strip()
    if not cls:
        errors["class"] = "Class is required."
    elif len(cls) > 20:
        errors["class"] = "Class is too long (max 20)."
    clean["class_name"] = cls

    try:
        marks = float(data.get("marks"))
        if not 0 <= marks <= 100:  # also rejects NaN
            raise ValueError
    except (TypeError, ValueError):
        errors["marks"] = "Marks must be a number between 0 and 100."
        marks = None
    clean["marks"] = marks

    contact = str(data.get("contact", "")).strip()
    if not re.fullmatch(r"[6-9]\d{9}", contact):
        errors["contact"] = "Enter a valid 10-digit mobile number."
    clean["contact"] = contact

    email = str(data.get("email") or "").strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors["email"] = "Email format is invalid."
    clean["email"] = email or None

    return clean, errors


def error(status, message, details=None):
    body = {"error": message}
    if details:
        body["details"] = details
    return jsonify(body), status


# ---------- routes ----------
@app.get("/api/students")
def list_students():
    """List all students; ?q=<text> searches by name or roll number."""
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        like = f"%{q}%"
        rows = db.execute(
            "SELECT * FROM students WHERE name LIKE ? OR roll_no LIKE ? ORDER BY roll_no",
            (like, like),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM students ORDER BY roll_no").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.get("/api/students/<int:sid>")
def get_student(sid):
    row = get_db().execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    if row is None:
        return error(404, "Student not found.")
    return jsonify(row_to_dict(row))


@app.post("/api/students")
def add_student():
    clean, errors = validate(request.get_json(silent=True))
    if errors:
        return error(400, "Validation failed.", errors)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO students (roll_no, name, class_name, marks, contact, email) "
            "VALUES (:roll_no, :name, :class_name, :marks, :contact, :email)",
            clean,
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error(409, "Roll number already exists.", {"roll_no": "Roll number already exists."})
    row = db.execute("SELECT * FROM students WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(row_to_dict(row)), 201


@app.put("/api/students/<int:sid>")
def update_student(sid):
    db = get_db()
    if db.execute("SELECT 1 FROM students WHERE id = ?", (sid,)).fetchone() is None:
        return error(404, "Student not found.")
    clean, errors = validate(request.get_json(silent=True))
    if errors:
        return error(400, "Validation failed.", errors)
    clean["id"] = sid
    try:
        db.execute(
            "UPDATE students SET roll_no=:roll_no, name=:name, class_name=:class_name, "
            "marks=:marks, contact=:contact, email=:email WHERE id=:id",
            clean,
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error(409, "Roll number already exists.", {"roll_no": "Roll number already exists."})
    row = db.execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    return jsonify(row_to_dict(row))


@app.delete("/api/students/<int:sid>")
def delete_student(sid):
    db = get_db()
    cur = db.execute("DELETE FROM students WHERE id = ?", (sid,))
    db.commit()
    if cur.rowcount == 0:
        return error(404, "Student not found.")
    return jsonify({"message": "Student deleted.", "id": sid})


@app.errorhandler(404)
def not_found(_e):
    return error(404, "Resource not found.")


@app.errorhandler(405)
def bad_method(_e):
    return error(405, "Method not allowed.")


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
