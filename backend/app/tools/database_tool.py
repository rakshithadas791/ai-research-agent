"""
database_tool.py
-----------------
SQLite-backed persistence. Two jobs:
  1. A "notes" table the AGENT ITSELF can write to/read from mid-task
     (exposed to the LLM as the save_note / get_notes tools) — this is
     the project's Database Tool and part of its State/Memory story.
  2. A "reports" table used by services/report_service.py to keep a
     history of every research run, backing the GET /api/reports endpoints.
"""
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join("data", "agent.db")


def _connect():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT, content TEXT, created_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal TEXT, content TEXT, path TEXT, created_at TEXT)""")
    return conn


def save_note(topic: str, content: str) -> str:
    conn = _connect()
    conn.execute("INSERT INTO notes (topic, content, created_at) VALUES (?, ?, ?)",
                 (topic, content, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()
    return f"Saved note under topic '{topic}'"


def get_notes(topic: str) -> str:
    conn = _connect()
    rows = conn.execute(
        "SELECT content, created_at FROM notes WHERE topic = ? ORDER BY id", (topic,)
    ).fetchall()
    conn.close()
    if not rows:
        return f"No notes found for topic '{topic}'"
    return "\n".join(f"- ({t}) {c}" for c, t in rows)


def save_report_record(goal: str, content: str, path: str) -> int:
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO reports (goal, content, path, created_at) VALUES (?, ?, ?, ?)",
        (goal, content, path, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    report_id = cur.lastrowid
    conn.close()
    return report_id


def list_report_records() -> list:
    conn = _connect()
    rows = conn.execute(
        "SELECT id, goal, path, created_at FROM reports ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [{"id": r[0], "goal": r[1], "path": r[2], "created_at": r[3]} for r in rows]


def get_report_record(report_id: int):
    conn = _connect()
    row = conn.execute(
        "SELECT id, goal, content, path, created_at FROM reports WHERE id = ?", (report_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "goal": row[1], "content": row[2], "path": row[3], "created_at": row[4]}
