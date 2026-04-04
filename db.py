"""
db.py — SQLite database layer for AgentX Bot
Handles users, chat history, memories, todos, notes.
"""

import sqlite3
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "agentx.db")


def get_conn():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize all database tables."""
    try:
        conn = get_conn()
        c = conn.cursor()

        # Users table
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                joined_at TEXT DEFAULT '',
                last_active TEXT DEFAULT '',
                message_count INTEGER DEFAULT 0
            )
        """)

        # Chat history
        c.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT DEFAULT 'user',
                content TEXT DEFAULT '',
                timestamp TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Memories
        c.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                key TEXT DEFAULT '',
                value TEXT DEFAULT '',
                timestamp TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Todo lists
        c.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task TEXT DEFAULT '',
                done INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Notes
        c.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT DEFAULT '',
                content TEXT DEFAULT '',
                timestamp TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Study materials
        c.execute("""
            CREATE TABLE IF NOT EXISTS study_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT DEFAULT '',
                content TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                timestamp TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Reminders
        c.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task TEXT DEFAULT '',
                remind_at TEXT DEFAULT '',
                done INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database init error: {e}")


# ── User Operations ──

def register_user(user_id: int, username: str = "", first_name: str = ""):
    """Register or update a user."""
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO users (user_id, username, first_name, joined_at, last_active)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_active=excluded.last_active
        """, (user_id, username, first_name, now, now))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Register user error: {e}")


def update_user_activity(user_id: int):
    """Update user's last active time and message count."""
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
            UPDATE users SET last_active=?, message_count=message_count+1
            WHERE user_id=?
        """, (now, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Update user activity error: {e}")


# ── Chat History ──

def save_message(user_id: int, role: str, content: str):
    """Save a chat message."""
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO chat_history (user_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, role, content, now))
        # Keep only last 50 messages per user
        c.execute("""
            DELETE FROM chat_history WHERE user_id=? AND id NOT IN (
                SELECT id FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT 50
            )
        """, (user_id, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Save message error: {e}")


def get_history(user_id: int, limit: int = 20) -> list:
    """Get chat history as list of dicts."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT role, content FROM chat_history
            WHERE user_id=? ORDER BY id DESC LIMIT ?
        """, (user_id, limit))
        rows = c.fetchall()
        conn.close()
        # Reverse to get chronological order
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    except Exception as e:
        logger.error(f"Get history error: {e}")
        return []


def clear_history(user_id: int) -> bool:
    """Clear chat history for a user."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        return False


# ── Memories ──

def save_memory(user_id: int, key: str, value: str):
    """Save a memory."""
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO memories (user_id, key, value, timestamp)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET value=excluded.value, timestamp=excluded.timestamp
        """, (user_id, key, value, now))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Save memory error: {e}")


def get_memories(user_id: int) -> list:
    """Get all memories for a user."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT key, value FROM memories WHERE user_id=? ORDER BY id DESC
        """, (user_id,))
        rows = c.fetchall()
        conn.close()
        return [{"key": r["key"], "value": r["value"]} for r in rows]
    except Exception as e:
        logger.error(f"Get memories error: {e}")
        return []


def delete_memory(user_id: int, key: str) -> bool:
    """Delete a memory by key."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM memories WHERE user_id=? AND key=?", (user_id, key))
        conn.commit()
        conn.close()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Delete memory error: {e}")
        return False


# ── Todos ──

def add_todo(user_id: int, task: str) -> int:
    """Add a todo item. Returns the todo id."""
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO todos (user_id, task, timestamp) VALUES (?, ?, ?)
        """, (user_id, task, now))
        conn.commit()
        todo_id = c.lastrowid
        conn.close()
        return todo_id
    except Exception as e:
        logger.error(f"Add todo error: {e}")
        return 0


def get_todos(user_id: int) -> list:
    """Get all todos for a user."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, task, done FROM todos WHERE user_id=? ORDER BY id ASC
        """, (user_id,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r["id"], "task": r["task"], "done": bool(r["done"])} for r in rows]
    except Exception as e:
        logger.error(f"Get todos error: {e}")
        return []


def toggle_todo(user_id: int, todo_id: int) -> bool:
    """Toggle a todo's done status."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            UPDATE todos SET done = CASE WHEN done=0 THEN 1 ELSE 0 END
            WHERE user_id=? AND id=?
        """, (user_id, todo_id))
        conn.commit()
        conn.close()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Toggle todo error: {e}")
        return False


def delete_todo(user_id: int, todo_id: int) -> bool:
    """Delete a todo."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM todos WHERE user_id=? AND id=?", (user_id, todo_id))
        conn.commit()
        conn.close()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Delete todo error: {e}")
        return False


# ── Notes ──

def save_note(user_id: int, title: str, content: str) -> int:
    """Save a note. Returns note id."""
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO notes (user_id, title, content, timestamp) VALUES (?, ?, ?, ?)
        """, (user_id, title, content, now))
        conn.commit()
        note_id = c.lastrowid
        conn.close()
        return note_id
    except Exception as e:
        logger.error(f"Save note error: {e}")
        return 0


def get_notes(user_id: int) -> list:
    """Get all notes for a user."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, title, content FROM notes WHERE user_id=? ORDER BY id DESC
        """, (user_id,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r["id"], "title": r["title"], "content": r["content"]} for r in rows]
    except Exception as e:
        logger.error(f"Get notes error: {e}")
        return []


def delete_note(user_id: int, note_id: int) -> bool:
    """Delete a note."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM notes WHERE user_id=? AND id=?", (user_id, note_id))
        conn.commit()
        conn.close()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Delete note error: {e}")
        return False


def get_note(user_id: int, note_id: int) -> dict:
    """Get a single note."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, title, content FROM notes WHERE user_id=? AND id=?
        """, (user_id, note_id))
        row = c.fetchone()
        conn.close()
        if row:
            return {"id": row["id"], "title": row["title"], "content": row["content"]}
        return None
    except Exception as e:
        logger.error(f"Get note error: {e}")
        return None


# ── Study Materials ──

def save_material(user_id: int, topic: str, content: str, tags: str = "") -> int:
    """Save study material. Returns material id."""
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO study_materials (user_id, topic, content, tags, timestamp) VALUES (?, ?, ?, ?, ?)
        """, (user_id, topic, content, tags, now))
        conn.commit()
        mat_id = c.lastrowid
        conn.close()
        return mat_id
    except Exception as e:
        logger.error(f"Save material error: {e}")
        return 0


def search_materials(user_id: int, keyword: str = "") -> list:
    """Search study materials by keyword."""
    try:
        conn = get_conn()
        c = conn.cursor()
        if keyword:
            c.execute("""
                SELECT id, topic, content, tags, timestamp FROM study_materials
                WHERE user_id=? AND (topic LIKE ? OR content LIKE ? OR tags LIKE ?)
                ORDER BY id DESC
            """, (user_id, f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
        else:
            c.execute("""
                SELECT id, topic, content, tags, timestamp FROM study_materials
                WHERE user_id=? ORDER BY id DESC
            """, (user_id,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r["id"], "topic": r["topic"], "content": r["content"],
                 "tags": r["tags"], "timestamp": r["timestamp"]} for r in rows]
    except Exception as e:
        logger.error(f"Search materials error: {e}")
        return []


def delete_material(user_id: int, material_id: int) -> bool:
    """Delete a study material."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM study_materials WHERE user_id=? AND id=?", (user_id, material_id))
        conn.commit()
        conn.close()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Delete material error: {e}")
        return False


# ── Reminders ──

def add_reminder(user_id: int, task: str, remind_at: str = "") -> int:
    """Add a reminder. Returns reminder id."""
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO reminders (user_id, task, remind_at, timestamp) VALUES (?, ?, ?, ?)
        """, (user_id, task, remind_at, now))
        conn.commit()
        rem_id = c.lastrowid
        conn.close()
        return rem_id
    except Exception as e:
        logger.error(f"Add reminder error: {e}")
        return 0


def get_reminders(user_id: int) -> list:
    """Get all reminders for a user."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, task, remind_at, done FROM reminders
            WHERE user_id=? ORDER BY id ASC
        """, (user_id,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r["id"], "task": r["task"], "remind_at": r["remind_at"],
                 "done": bool(r["done"])} for r in rows]
    except Exception as e:
        logger.error(f"Get reminders error: {e}")
        return []


def delete_reminder(user_id: int, reminder_id: int) -> bool:
    """Delete a reminder."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM reminders WHERE user_id=? AND id=?", (user_id, reminder_id))
        conn.commit()
        conn.close()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Delete reminder error: {e}")
        return False
