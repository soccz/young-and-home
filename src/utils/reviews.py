"""
지역 후기 시스템 — SQLite 기반
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "young_home.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS district_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment TEXT,
            user_status TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    return conn


def add_review(district: str, rating: int, comment: str, user_status: str = ""):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO district_reviews (district, rating, comment, user_status) VALUES (?, ?, ?, ?)",
        (district, rating, comment, user_status)
    )
    conn.commit()
    conn.close()


def get_reviews(district: str, limit: int = 10):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT rating, comment, user_status, created_at FROM district_reviews WHERE district = ? ORDER BY created_at DESC LIMIT ?",
        (district, limit)
    ).fetchall()
    conn.close()
    return [{"rating": r[0], "comment": r[1], "status": r[2], "date": r[3]} for r in rows]


def get_avg_rating(district: str):
    conn = _get_conn()
    row = conn.execute(
        "SELECT AVG(rating), COUNT(*) FROM district_reviews WHERE district = ?",
        (district,)
    ).fetchone()
    conn.close()
    return {"avg": round(row[0], 1) if row[0] else 0, "count": row[1] or 0}
