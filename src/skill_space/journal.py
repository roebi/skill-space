"""Journal — learning events (claim, done) stored in SQLite."""

from __future__ import annotations

from datetime import datetime, timezone

from skill_space.store import Store


class Journal:
    def __init__(self) -> None:
        self.store = Store()

    def claim(self, skill_name: str) -> None:
        self.store.conn.execute(
            "INSERT INTO learning_journal(skill_name, event, timestamp) VALUES (?, 'claimed', ?)",
            (skill_name, datetime.now(timezone.utc).isoformat()),
        )
        self.store.conn.commit()

    def done(self, skill_name: str, level: int) -> None:
        self.store.conn.execute(
            "INSERT INTO learning_journal(skill_name, event, level, timestamp) VALUES (?, 'done', ?, ?)",
            (skill_name, level, datetime.now(timezone.utc).isoformat()),
        )
        self.store.conn.commit()

    def completed_names(self) -> set[str]:
        cur = self.store.conn.execute(
            "SELECT DISTINCT skill_name FROM learning_journal WHERE event='done'"
        )
        return {row[0] for row in cur.fetchall()}

    def max_level(self, skill_name: str) -> int:
        cur = self.store.conn.execute(
            "SELECT MAX(level) FROM learning_journal WHERE skill_name=? AND event='done'",
            (skill_name,),
        )
        val = cur.fetchone()[0]
        return val or 0
