"""
AgentX v2 — Database
SQLite, zero config, runs everywhere.
"""
import sqlite3
import json
import os
from datetime import datetime


class DB:
    def __init__(self, path="data/agentx.db"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init()

    def _init(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                name TEXT DEFAULT '',
                model TEXT DEFAULT 'pollinations',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                ts TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                ts TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, key)
            );
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT,
                front TEXT,
                back TEXT
            );
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT,
                questions TEXT,
                score TEXT DEFAULT ''
            );
        """)
        self.conn.commit()

    # Users
    def save_user(self, uid, username, name):
        self.conn.execute(
            "INSERT OR REPLACE INTO users (user_id, username, name, created_at) VALUES (?,?,?,datetime('now'))",
            (uid, username, name),
        )
        self.conn.commit()

    def get_user(self, uid):
        r = self.conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
        return dict(r) if r else None

    # Messages (chat history)
    def save_msg(self, uid, role, content):
        self.conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?,?,?)",
            (uid, role, content[:4000]),
        )
        self.conn.commit()

    def get_history(self, uid, limit=20):
        rows = self.conn.execute(
            "SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (uid, limit),
        ).fetchall()
        return list(reversed([dict(r) for r in rows]))

    def clear_history(self, uid):
        self.conn.execute("DELETE FROM messages WHERE user_id=?", (uid,))
        self.conn.commit()

    # Memory
    def save_memory(self, uid, key, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO memory (user_id, key, value) VALUES (?,?,?)",
            (uid, key, value),
        )
        self.conn.commit()

    def get_memories(self, uid):
        rows = self.conn.execute(
            "SELECT key, value FROM memory WHERE user_id=?", (uid,)
        ).fetchall()
        return {r["key"]: r["value"] for r in rows}

    def delete_memory(self, uid, key):
        self.conn.execute("DELETE FROM memory WHERE user_id=? AND key=?", (uid, key))
        self.conn.commit()

    # Flashcards
    def save_flashcards(self, uid, topic, cards):
        for front, back in cards:
            self.conn.execute(
                "INSERT INTO flashcards (user_id, topic, front, back) VALUES (?,?,?,?)",
                (uid, topic, front, back),
            )
        self.conn.commit()

    def get_flashcards(self, uid):
        rows = self.conn.execute(
            "SELECT front, back, topic FROM flashcards WHERE user_id=? ORDER BY id",
            (uid,),
        ).fetchall()
        return [dict(r) for r in rows]

    # Quizzes
    def save_quiz(self, uid, topic, questions):
        self.conn.execute(
            "INSERT INTO quizzes (user_id, topic, questions) VALUES (?,?,?)",
            (uid, topic, json.dumps(questions)),
        )
        self.conn.commit()

    def get_quizzes(self, uid):
        rows = self.conn.execute(
            "SELECT topic, questions, score FROM quizzes WHERE user_id=? ORDER BY id DESC LIMIT 5",
            (uid,),
        ).fetchall()
        return [dict(r) for r in rows]
