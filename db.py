import sqlite3
import os
from flask import g, current_app


def db_init(app):
    # default DATABASE config should be provided by app (can be overridden in tests)
    app.config.setdefault("DATABASE", os.path.join(app.instance_path, "app.db"))
    # ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception:
        pass

    # create table schema if not exists
    db_path = app.config["DATABASE"]
    uri = db_path.startswith("file:")
    conn = sqlite3.connect(db_path, uri=uri)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            full_name TEXT,
            vehicle_type TEXT,
            latitude REAL,
            longitude REAL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT
        )
        """
    )
    # Add password_hash column if it doesn't exist
    try:
        cur.execute("ALTER TABLE user_profiles ADD COLUMN password_hash TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    # Add is_admin column if it doesn't exist
    try:
        cur.execute("ALTER TABLE user_profiles ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()


def get_db():
    if "db" not in g:
        db_path = current_app.config["DATABASE"]
        conn = sqlite3.connect(db_path, uri=db_path.startswith("file:"))
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()
