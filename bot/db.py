"""Stockage SQLite des avertissements."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Warning:
    id: int
    user_id: int
    moderator_id: int
    reason: str
    created_at: int


class Database:
    def __init__(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_warnings_user ON warnings (guild_id, user_id)"
        )
        self.conn.commit()

    def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO warnings (guild_id, user_id, moderator_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, reason, int(time.time())),
        )
        self.conn.commit()
        return cur.lastrowid

    def list_warnings(self, guild_id: int, user_id: int) -> list[Warning]:
        rows = self.conn.execute(
            "SELECT id, user_id, moderator_id, reason, created_at FROM warnings "
            "WHERE guild_id = ? AND user_id = ? ORDER BY id",
            (guild_id, user_id),
        ).fetchall()
        return [Warning(*row) for row in rows]

    def count_warnings(self, guild_id: int, user_id: int) -> int:
        (count,) = self.conn.execute(
            "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
        ).fetchone()
        return count

    def delete_warning(self, guild_id: int, warning_id: int) -> bool:
        cur = self.conn.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND id = ?", (guild_id, warning_id)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def clear_warnings(self, guild_id: int, user_id: int) -> int:
        cur = self.conn.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
        )
        self.conn.commit()
        return cur.rowcount

    def close(self) -> None:
        self.conn.close()
