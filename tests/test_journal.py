"""Tests for journal.py — claim, done, completed_names, max_level."""

import pytest

from skill_space import store as store_mod


@pytest.fixture()
def journal(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DB_PATH", tmp_path / "space.db")
    from skill_space.journal import Journal

    return Journal()


def test_claim_records_event(journal):
    journal.claim("some-skill-en")
    cur = journal.store.conn.execute(
        "SELECT event FROM learning_journal WHERE skill_name='some-skill-en'"
    )
    assert cur.fetchone()[0] == "claimed"


def test_done_records_event_and_level(journal):
    journal.done("some-skill-en", level=3)
    cur = journal.store.conn.execute(
        "SELECT event, level FROM learning_journal WHERE skill_name='some-skill-en'"
    )
    row = cur.fetchone()
    assert row[0] == "done"
    assert row[1] == 3


def test_completed_names_empty(journal):
    assert journal.completed_names() == set()


def test_completed_names_after_done(journal):
    journal.done("skill-a-en", level=4)
    journal.done("skill-b-en", level=2)
    assert journal.completed_names() == {"skill-a-en", "skill-b-en"}


def test_completed_names_excludes_claimed_only(journal):
    journal.claim("skill-a-en")
    assert journal.completed_names() == set()


def test_max_level_no_events(journal):
    assert journal.max_level("skill-a-en") == 0


def test_max_level_single(journal):
    journal.done("skill-a-en", level=3)
    assert journal.max_level("skill-a-en") == 3


def test_max_level_multiple_sessions(journal):
    journal.done("skill-a-en", level=2)
    journal.done("skill-a-en", level=4)
    journal.done("skill-a-en", level=3)
    assert journal.max_level("skill-a-en") == 4


def test_claim_and_done_independent(journal):
    journal.claim("skill-a-en")
    journal.done("skill-a-en", level=5)
    assert "skill-a-en" in journal.completed_names()
    assert journal.max_level("skill-a-en") == 5
