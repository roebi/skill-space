"""Store — SQLite + sqlite-vec persistence layer for the Skill Space."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from rich.console import Console
from rich.table import Table

DB_PATH = Path.home() / ".skill-space" / "space.db"
console = Console()


CREATE_SKILLS = """
CREATE TABLE IF NOT EXISTS skills (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    skill_class   TEXT,          -- Role | Topic | Process | OneStepProcess
    crud_verb     TEXT,
    topic         TEXT,
    requires_role TEXT,
    language      TEXT DEFAULT 'en',
    repo_url      TEXT,
    repo_trust    TEXT DEFAULT 'high',  -- high | medium | low
    pinned_commit TEXT,
    fuzzy_tags    TEXT,          -- JSON array of strings
    description   TEXT,
    last_indexed  TEXT           -- ISO-8601
);
"""

CREATE_REPOS = """
CREATE TABLE IF NOT EXISTS repos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT NOT NULL UNIQUE,
    trust       TEXT DEFAULT 'high',
    last_synced TEXT
);
"""

CREATE_JOURNAL = """
CREATE TABLE IF NOT EXISTS learning_journal (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    event      TEXT NOT NULL,   -- 'claimed' | 'done'
    level      INTEGER,
    timestamp  TEXT NOT NULL    -- ISO-8601
);
"""

# sqlite-vec virtual table for embeddings (created after vec extension loaded)
CREATE_SKILL_VECS = """
CREATE VIRTUAL TABLE IF NOT EXISTS skill_vecs USING vec0(
    skill_id INTEGER PRIMARY KEY,
    embedding FLOAT[384]
);
"""


class Store:
    def __init__(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._init_schema()

    def _init_schema(self) -> None:
        try:
            import sqlite_vec  # type: ignore
            self.conn.load_extension(sqlite_vec.loadable_path())
            self.conn.execute(CREATE_SKILL_VECS)
        except Exception:
            console.print("[yellow]sqlite-vec not available — vector search disabled.[/yellow]")
        self.conn.executescript(CREATE_SKILLS + CREATE_REPOS + CREATE_JOURNAL)
        self.conn.commit()

    def upsert_skill(self, skill: dict) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO skills
                (name, skill_class, crud_verb, topic, requires_role, language,
                 repo_url, repo_trust, pinned_commit, fuzzy_tags, description, last_indexed)
            VALUES
                (:name, :skill_class, :crud_verb, :topic, :requires_role, :language,
                 :repo_url, :repo_trust, :pinned_commit, :fuzzy_tags, :description, :last_indexed)
            ON CONFLICT(name) DO UPDATE SET
                skill_class=excluded.skill_class,
                crud_verb=excluded.crud_verb,
                topic=excluded.topic,
                requires_role=excluded.requires_role,
                fuzzy_tags=excluded.fuzzy_tags,
                description=excluded.description,
                last_indexed=excluded.last_indexed
            RETURNING id
            """,
            skill,
        )
        self.conn.commit()
        return cur.fetchone()[0]

    def store_embedding(self, skill_id: int, vector: list[float]) -> None:
        import json
        self.conn.execute(
            "INSERT OR REPLACE INTO skill_vecs(skill_id, embedding) VALUES (?, ?)",
            (skill_id, json.dumps(vector)),
        )
        self.conn.commit()

    def all_skills(self) -> list[dict]:
        cur = self.conn.execute("SELECT * FROM skills")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def print_stats(self) -> None:
        skill_count = self.conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
        repo_count = self.conn.execute("SELECT COUNT(*) FROM repos").fetchone()[0]
        journal_count = self.conn.execute("SELECT COUNT(*) FROM learning_journal").fetchone()[0]

        t = Table(title="Skill Space Stats")
        t.add_column("Metric")
        t.add_column("Value", style="cyan")
        t.add_row("Skills indexed", str(skill_count))
        t.add_row("Repos configured", str(repo_count))
        t.add_row("Learning events", str(journal_count))
        t.add_row("DB path", str(DB_PATH))
        console.print(t)
