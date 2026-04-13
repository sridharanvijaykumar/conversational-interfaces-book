"""
Database Storage for Conversation History
Chapter 11: Architecture & Backend Integration

Demonstrates how to persist conversation data using SQLite (for local
development) and shows the same interface pattern you'd use with
PostgreSQL or MongoDB in production.

Tables:
  sessions     — one row per conversation session
  messages     — one row per turn (user + bot message pair)
  user_profiles — persistent user preferences across sessions
"""

import sqlite3
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict
from contextlib import contextmanager
from dataclasses import dataclass, asdict


# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

@dataclass
class Session:
    session_id:  str
    user_id:     Optional[str]
    channel:     str            # "web", "whatsapp", "voice", etc.
    created_at:  str
    updated_at:  str
    is_active:   bool = True
    metadata:    Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Message:
    message_id:  str
    session_id:  str
    turn:        int
    user_text:   str
    bot_text:    str
    intent:      str
    confidence:  float
    timestamp:   str
    entities:    Dict = None

    def __post_init__(self):
        if self.entities is None:
            self.entities = {}


@dataclass
class UserProfile:
    user_id:     str
    name:        Optional[str]
    language:    str
    preferences: Dict
    created_at:  str
    updated_at:  str


# ─────────────────────────────────────────────
# Database manager
# ─────────────────────────────────────────────

class ConversationDB:
    """
    SQLite-backed conversation store.
    Swap the connection string to use PostgreSQL (via psycopg2)
    or any other database in production.
    """

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")   # Better concurrent read performance
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Create tables if they don't already exist."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id  TEXT PRIMARY KEY,
                    user_id     TEXT,
                    channel     TEXT NOT NULL DEFAULT 'web',
                    is_active   INTEGER NOT NULL DEFAULT 1,
                    metadata    TEXT,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    message_id  TEXT PRIMARY KEY,
                    session_id  TEXT NOT NULL REFERENCES sessions(session_id),
                    turn        INTEGER NOT NULL,
                    user_text   TEXT NOT NULL,
                    bot_text    TEXT NOT NULL,
                    intent      TEXT,
                    confidence  REAL,
                    entities    TEXT,
                    timestamp   TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id     TEXT PRIMARY KEY,
                    name        TEXT,
                    language    TEXT NOT NULL DEFAULT 'en',
                    preferences TEXT,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_user
                    ON sessions(user_id);
            """)

    # ── Sessions ──────────────────────────────

    def create_session(
        self,
        user_id: Optional[str] = None,
        channel: str = "web",
        metadata: Optional[Dict] = None,
    ) -> Session:
        now = datetime.utcnow().isoformat()
        session = Session(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            channel=channel,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO sessions
                   (session_id, user_id, channel, is_active, metadata, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session.session_id, session.user_id, session.channel,
                 int(session.is_active), json.dumps(session.metadata),
                 session.created_at, session.updated_at)
            )
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if not row:
            return None
        return Session(
            session_id=row["session_id"],
            user_id=row["user_id"],
            channel=row["channel"],
            is_active=bool(row["is_active"]),
            metadata=json.loads(row["metadata"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def end_session(self, session_id: str):
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET is_active = 0, updated_at = ? WHERE session_id = ?",
                (now, session_id)
            )

    # ── Messages ──────────────────────────────

    def save_message(
        self,
        session_id:  str,
        turn:        int,
        user_text:   str,
        bot_text:    str,
        intent:      str      = "unknown",
        confidence:  float    = 0.0,
        entities:    Optional[Dict] = None,
    ) -> Message:
        msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            turn=turn,
            user_text=user_text,
            bot_text=bot_text,
            intent=intent,
            confidence=confidence,
            entities=entities or {},
            timestamp=datetime.utcnow().isoformat(),
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO messages
                   (message_id, session_id, turn, user_text, bot_text,
                    intent, confidence, entities, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (msg.message_id, msg.session_id, msg.turn,
                 msg.user_text, msg.bot_text,
                 msg.intent, msg.confidence,
                 json.dumps(msg.entities), msg.timestamp)
            )
            # Update session timestamp
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (msg.timestamp, session_id)
            )
        return msg

    def get_history(self, session_id: str) -> List[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY turn ASC",
                (session_id,)
            ).fetchall()
        return [
            Message(
                message_id=r["message_id"],
                session_id=r["session_id"],
                turn=r["turn"],
                user_text=r["user_text"],
                bot_text=r["bot_text"],
                intent=r["intent"],
                confidence=r["confidence"],
                entities=json.loads(r["entities"] or "{}"),
                timestamp=r["timestamp"],
            )
            for r in rows
        ]

    # ── User profiles ─────────────────────────

    def upsert_user_profile(
        self,
        user_id:     str,
        name:        Optional[str]  = None,
        language:    str            = "en",
        preferences: Optional[Dict] = None,
    ) -> UserProfile:
        now = datetime.utcnow().isoformat()
        profile = UserProfile(
            user_id=user_id, name=name, language=language,
            preferences=preferences or {},
            created_at=now, updated_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO user_profiles
                   (user_id, name, language, preferences, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                       name=excluded.name,
                       language=excluded.language,
                       preferences=excluded.preferences,
                       updated_at=excluded.updated_at""",
                (profile.user_id, profile.name, profile.language,
                 json.dumps(profile.preferences),
                 profile.created_at, profile.updated_at)
            )
        return profile

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
        if not row:
            return None
        return UserProfile(
            user_id=row["user_id"], name=row["name"],
            language=row["language"],
            preferences=json.loads(row["preferences"] or "{}"),
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    # ── Analytics helpers ─────────────────────

    def get_intent_stats(self) -> List[Dict]:
        """Return intent frequency counts across all messages."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT intent, COUNT(*) as count,
                          AVG(confidence) as avg_confidence
                   FROM messages
                   GROUP BY intent
                   ORDER BY count DESC"""
            ).fetchall()
        return [dict(r) for r in rows]

    def get_session_stats(self) -> Dict:
        """Return aggregate session statistics."""
        with self._connect() as conn:
            stats = conn.execute(
                """SELECT
                       COUNT(*) as total_sessions,
                       SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) as active_sessions,
                       (SELECT COUNT(*) FROM messages) as total_messages
                   FROM sessions"""
            ).fetchone()
        return dict(stats)


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────

def demo():
    import os
    db_file = "demo_conversations.db"

    print("=== Database Storage Demo ===\n")
    db = ConversationDB(db_path=db_file)

    # Create a user profile
    user = db.upsert_user_profile(
        user_id="user_001",
        name="Priya",
        language="en",
        preferences={"notifications": True, "theme": "light"},
    )
    print(f"User profile created: {user.name} ({user.user_id})")

    # Start a session
    session = db.create_session(user_id="user_001", channel="web")
    print(f"Session created: {session.session_id[:8]}…")

    # Simulate a conversation
    exchanges = [
        ("Hello!", "Hi there! How can I help you today?", "greeting", 0.95),
        ("What are your opening hours?", "We're open Mon–Fri, 9 AM–6 PM IST.", "hours", 0.88),
        ("Thanks!", "You're welcome! Have a great day!", "thanks", 0.92),
    ]

    for turn, (user_msg, bot_msg, intent, conf) in enumerate(exchanges, start=1):
        db.save_message(
            session_id=session.session_id,
            turn=turn,
            user_text=user_msg,
            bot_text=bot_msg,
            intent=intent,
            confidence=conf,
        )
        print(f"  Turn {turn} saved — intent: {intent}")

    # Retrieve and display history
    print(f"\nConversation history for session {session.session_id[:8]}…:")
    for msg in db.get_history(session.session_id):
        print(f"  [{msg.turn}] User: {msg.user_text}")
        print(f"       Bot:  {msg.bot_text}")

    # Print stats
    print("\nSession stats:", db.get_session_stats())
    print("Intent stats:")
    for stat in db.get_intent_stats():
        print(f"  {stat['intent']:20s}  count={stat['count']}  avg_conf={stat['avg_confidence']:.2f}")

    # Clean up demo file
    db.end_session(session.session_id)
    os.remove(db_file)
    print(f"\nDemo complete. (Demo DB file removed.)")


if __name__ == "__main__":
    demo()
