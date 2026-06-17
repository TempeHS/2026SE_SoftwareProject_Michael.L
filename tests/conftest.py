import os
import sqlite3
import sys
import importlib
import pytest


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    # Required env before importing main.py
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    db_path = tmp_path / "test_auth.db"
    monkeypatch.setenv("AUTH_DB", str(db_path))

    # Bootstrap minimal tables so main.init_auth_db() can run
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            totp_secret TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS huddle_group_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, role)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS huddle_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            start_date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    # Fresh import each test
    if "main" in sys.modules:
        del sys.modules["main"]
    mod = importlib.import_module("main")
    return mod
