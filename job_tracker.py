import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "job_tracker.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        position TEXT NOT NULL,
        track TEXT NOT NULL,
        fit_score INTEGER NOT NULL,
        url TEXT,
        status TEXT DEFAULT 'PENDING_REVIEW', -- 'PENDING_REVIEW', 'APPLIED', 'INTERVIEW', 'REJECTED', 'OFFER'
        date_added TEXT,
        notes TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_application(company: str, position: str, track: str, fit_score: int, url: str = "", notes: str = "") -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("""
    INSERT INTO applications (company, position, track, fit_score, url, status, date_added, notes)
    VALUES (?, ?, ?, ?, ?, 'PENDING_REVIEW', ?, ?)
    """, (company, position, track, fit_score, url, today, notes))
    app_id = cur.lastrowid
    conn.commit()
    conn.close()
    return app_id

def list_applications(status: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM applications WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cur.execute("SELECT * FROM applications ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_status(app_id: int, new_status: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, app_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos de seguimiento inicializada en:", DB_PATH)
