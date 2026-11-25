import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parents[1] / "data" / "jakicha.db"))


def connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL, role TEXT NOT NULL, message TEXT NOT NULL,
            guest_name TEXT DEFAULT '', created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL, guest_name TEXT DEFAULT '', checkin TEXT NOT NULL,
            checkout TEXT NOT NULL, guests TEXT NOT NULL, room_type TEXT DEFAULT '',
            notes TEXT DEFAULT '', status TEXT DEFAULT 'pending', created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
            phone TEXT PRIMARY KEY, state TEXT DEFAULT 'idle', data TEXT DEFAULT '{}',
            updated_at TEXT NOT NULL
        )""")
        conn.commit()


def save_message(phone, role, message, guest_name=""):
    with connect() as conn:
        conn.execute(
            "INSERT INTO messages(phone,role,message,guest_name,created_at) VALUES(?,?,?,?,?)",
            (phone, role, message, guest_name, datetime.utcnow().isoformat(timespec="seconds"))
        )
        conn.commit()


def get_session(phone):
    import json
    with connect() as conn:
        row = conn.execute("SELECT state,data FROM sessions WHERE phone=?", (phone,)).fetchone()
    if not row:
        return "idle", {}
    try:
        return row["state"], json.loads(row["data"] or "{}")
    except Exception:
        return "idle", {}


def set_session(phone, state, data):
    import json
    with connect() as conn:
        conn.execute("""INSERT INTO sessions(phone,state,data,updated_at) VALUES(?,?,?,?)
            ON CONFLICT(phone) DO UPDATE SET state=excluded.state,data=excluded.data,updated_at=excluded.updated_at""",
            (phone, state, json.dumps(data, ensure_ascii=False), datetime.utcnow().isoformat(timespec="seconds")))
        conn.commit()


def create_booking(phone, name, data):
    with connect() as conn:
        cur = conn.execute("""INSERT INTO bookings
            (phone,guest_name,checkin,checkout,guests,room_type,notes,status,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (phone, name, data["checkin"], data["checkout"], data["guests"],
             data.get("room_type", ""), data.get("notes", ""), "pending",
             datetime.utcnow().isoformat(timespec="seconds")))
        conn.commit()
        return cur.lastrowid


def get_stats():
    with connect() as conn:
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        guests = conn.execute("SELECT COUNT(DISTINCT phone) FROM messages").fetchone()[0]
        total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM bookings WHERE status='pending'").fetchone()[0]
        confirmed = conn.execute("SELECT COUNT(*) FROM bookings WHERE status='confirmed'").fetchone()[0]
    return {"messages": total_messages, "guests": guests, "bookings": total_bookings,
            "pending": pending, "confirmed": confirmed}


def get_recent_bookings(limit=50):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM bookings ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_booking(booking_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    return dict(row) if row else None


def update_booking_status(booking_id, status):
    with connect() as conn:
        conn.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
        conn.commit()


def get_recent_messages(limit=30):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
