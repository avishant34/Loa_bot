import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional, List
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "loa_bot.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            language TEXT DEFAULT 'hi',
            daily_enabled INTEGER DEFAULT 0,
            daily_time TEXT DEFAULT '08:00',
            streak INTEGER DEFAULT 0,
            last_active DATE,
            is_premium INTEGER DEFAULT 0,
            premium_until DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration for existing DBs
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
    except:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN premium_until DATE")
    except:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal_text TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gratitude (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            entry_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS affirmations_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            affirmation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Daily usage tracking for free limits
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage (
            user_id INTEGER,
            usage_date DATE,
            chat_count INTEGER DEFAULT 0,
            affirmation_count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, usage_date)
        )
    """)

    # Payment / subscription logs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            amount INTEGER,
            days INTEGER,
            activated_by TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()


def ensure_user(user_id: int, username: str = None, first_name: str = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, username, first_name, last_active) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, date.today().isoformat())
        )
    else:
        cur.execute(
            "UPDATE users SET username = ?, first_name = ?, last_active = ? WHERE user_id = ?",
            (username, first_name, date.today().isoformat(), user_id)
        )
    conn.commit()
    conn.close()


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def is_premium(user_id: int) -> bool:
    """Check if user currently has active premium."""
    u = get_user(user_id)
    if not u:
        return False
    if not u["is_premium"]:
        return False
    if u["premium_until"]:
        try:
            until = date.fromisoformat(u["premium_until"])
            if until < date.today():
                # Expired → auto revoke
                set_premium(user_id, False)
                return False
            return True
        except:
            return bool(u["is_premium"])
    return bool(u["is_premium"])


def set_premium(user_id: int, active: bool, days: int = 30, activated_by: str = "admin", note: str = ""):
    conn = get_connection()
    cur = conn.cursor()

    if active:
        until = (date.today() + timedelta(days=days)).isoformat()
        cur.execute(
            "UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?",
            (until, user_id)
        )
        # Log
        plan = f"{days} days"
        cur.execute(
            "INSERT INTO subscriptions (user_id, plan, amount, days, activated_by, note) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, plan, 0, days, activated_by, note)
        )
    else:
        cur.execute(
            "UPDATE users SET is_premium = 0, premium_until = NULL WHERE user_id = ?",
            (user_id,)
        )

    conn.commit()
    conn.close()


def get_premium_until(user_id: int) -> Optional[str]:
    u = get_user(user_id)
    if u and u["premium_until"]:
        return u["premium_until"]
    return None


def set_daily(user_id: int, enabled: bool, time_str: str = "08:00"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET daily_enabled = ?, daily_time = ? WHERE user_id = ?",
        (1 if enabled else 0, time_str, user_id)
    )
    conn.commit()
    conn.close()


def update_streak(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT streak, last_active FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return 0

    today = date.today()
    last = date.fromisoformat(row["last_active"]) if row["last_active"] else None
    streak = row["streak"] or 0

    if last == today:
        pass
    elif last and (today - last).days == 1:
        streak += 1
    else:
        streak = 1

    cur.execute(
        "UPDATE users SET streak = ?, last_active = ? WHERE user_id = ?",
        (streak, today.isoformat(), user_id)
    )
    conn.commit()
    conn.close()
    return streak


def add_goal(user_id: int, goal_text: str, category: str = "general") -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO goals (user_id, goal_text, category) VALUES (?, ?, ?)",
        (user_id, goal_text.strip(), category)
    )
    goal_id = cur.lastrowid
    conn.commit()
    conn.close()
    return goal_id


def get_active_goals(user_id: int) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM goals WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def count_active_goals(user_id: int) -> int:
    return len(get_active_goals(user_id))


def deactivate_goal(user_id: int, goal_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE goals SET is_active = 0 WHERE id = ? AND user_id = ?",
        (goal_id, user_id)
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def add_gratitude(user_id: int, text: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO gratitude (user_id, entry_text) VALUES (?, ?)",
        (user_id, text.strip())
    )
    entry_id = cur.lastrowid
    conn.commit()
    conn.close()
    update_streak(user_id)
    return entry_id


def get_recent_gratitude(user_id: int, limit: int = 5) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM gratitude WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def log_affirmation(user_id: int, text: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO affirmations_log (user_id, affirmation) VALUES (?, ?)",
        (user_id, text)
    )
    conn.commit()
    conn.close()
    update_streak(user_id)
    # Also count usage
    increment_usage(user_id, "affirmation")


def get_all_daily_users() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE daily_enabled = 1")
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------- Usage Limits (Free plan) ----------

def _get_or_create_usage(user_id: int):
    today = date.today().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM daily_usage WHERE user_id = ? AND usage_date = ?",
        (user_id, today)
    )
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO daily_usage (user_id, usage_date, chat_count, affirmation_count) VALUES (?, ?, 0, 0)",
            (user_id, today)
        )
        conn.commit()
        cur.execute(
            "SELECT * FROM daily_usage WHERE user_id = ? AND usage_date = ?",
            (user_id, today)
        )
        row = cur.fetchone()
    conn.close()
    return row


def increment_usage(user_id: int, kind: str = "chat"):
    today = date.today().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    _get_or_create_usage(user_id)  # ensure row exists

    if kind == "chat":
        cur.execute(
            "UPDATE daily_usage SET chat_count = chat_count + 1 WHERE user_id = ? AND usage_date = ?",
            (user_id, today)
        )
    else:
        cur.execute(
            "UPDATE daily_usage SET affirmation_count = affirmation_count + 1 WHERE user_id = ? AND usage_date = ?",
            (user_id, today)
        )
    conn.commit()
    conn.close()


def get_usage(user_id: int) -> dict:
    row = _get_or_create_usage(user_id)
    return {
        "chat_count": row["chat_count"] if row else 0,
        "affirmation_count": row["affirmation_count"] if row else 0,
    }


# Free plan limits
FREE_CHAT_LIMIT = 8
FREE_AFFIRMATION_LIMIT = 5
FREE_GOAL_LIMIT = 3


def can_use_chat(user_id: int) -> tuple[bool, str]:
    if is_premium(user_id):
        return True, ""
    usage = get_usage(user_id)
    if usage["chat_count"] >= FREE_CHAT_LIMIT:
        return False, f"Aaj ka free AI chat limit ({FREE_CHAT_LIMIT}) khatam ho gaya.\n\nPremium lo → Unlimited chat\n/premium"
    return True, ""


def can_use_affirmation(user_id: int) -> tuple[bool, str]:
    if is_premium(user_id):
        return True, ""
    usage = get_usage(user_id)
    if usage["affirmation_count"] >= FREE_AFFIRMATION_LIMIT:
        return False, f"Aaj ka free affirmation limit ({FREE_AFFIRMATION_LIMIT}) khatam.\n\nPremium → Unlimited\n/premium"
    return True, ""


def can_add_goal(user_id: int) -> tuple[bool, str]:
    if is_premium(user_id):
        return True, ""
    count = count_active_goals(user_id)
    if count >= FREE_GOAL_LIMIT:
        return False, f"Free plan mein max {FREE_GOAL_LIMIT} goals allowed hain.\n\nPremium → Unlimited goals\n/premium"
    return True, ""
