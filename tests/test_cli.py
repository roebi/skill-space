"""Integration tests for cli.py — typer commands via CliRunner."""

import pytest
from typer.testing import CliRunner

from skill_space.cli import app
from skill_space import store as store_mod

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DB_PATH", tmp_path / "space.db")


# ── space stats ────────────────────────────────────────────────────────────────


def test_space_stats_runs():
    result = runner.invoke(app, ["space", "stats"])
    assert result.exit_code == 0
    assert "Skills indexed" in result.output


# ── space drift ────────────────────────────────────────────────────────────────


def test_space_drift_runs():
    result = runner.invoke(app, ["space", "drift"])
    assert result.exit_code == 0


# ── learn claim ────────────────────────────────────────────────────────────────


def test_learn_claim_success():
    result = runner.invoke(app, ["learn", "claim", "some-skill-en"])
    assert result.exit_code == 0
    assert "Claimed" in result.output
    assert "some-skill-en" in result.output


# ── learn done ─────────────────────────────────────────────────────────────────


def test_learn_done_success():
    result = runner.invoke(app, ["learn", "done", "some-skill-en", "--level", "3"])
    assert result.exit_code == 0
    assert "Done" in result.output
    assert "level 3" in result.output


def test_learn_done_invalid_level():
    result = runner.invoke(app, ["learn", "done", "some-skill-en", "--level", "9"])
    assert result.exit_code != 0


# ── learn next ─────────────────────────────────────────────────────────────────


def test_learn_next_empty_space():
    result = runner.invoke(app, ["learn", "next"])
    assert result.exit_code == 0
    assert "No suggestion" in result.output


def test_learn_next_with_skill(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DB_PATH", tmp_path / "space.db")
    from skill_space.store import Store

    Store().upsert_skill(
        {
            "name": "test-skill-en",
            "skill_class": "Topic",
            "crud_verb": None,
            "topic": "testing",
            "requires_role": None,
            "language": "en",
            "repo_url": "https://github.com/test/repo",
            "repo_trust": "high",
            "pinned_commit": "abc123",
            "fuzzy_tags": '["testing"]',
            "description": "A test skill",
            "last_indexed": "2026-01-01T00:00:00+00:00",
        }
    )
    result = runner.invoke(app, ["learn", "next"])
    assert result.exit_code == 0
    assert "test-skill-en" in result.output


# ── search read (template matching) ───────────────────────────────────────────


def test_search_read_empty_space():
    result = runner.invoke(app, ["search", "read", "topic=*"])
    assert result.exit_code == 0
    assert "No matches" in result.output


# ── help ──────────────────────────────────────────────────────────────────────


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Fuzzy Tuple Space" in result.output
