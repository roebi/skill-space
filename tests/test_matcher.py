"""Tests for matcher.py — fuzzy membership functions and template parsing."""

import pytest

from skill_space.matcher import (
    Matcher,
    SkillMatch,
    fuzzy_class_match,
    fuzzy_token_overlap,
    fuzzy_trust,
    parse_template,
)


# ── fuzzy_class_match ──────────────────────────────────────────────────────────


def test_class_match_exact():
    assert fuzzy_class_match("Process", "Process") == 1.0


def test_class_match_adjacent():
    score = fuzzy_class_match("Process", "OneStepProcess")
    assert 0.5 < score < 1.0


def test_class_match_unrelated():
    assert fuzzy_class_match("Role", "Process") == 0.0


def test_class_match_none_query():
    assert fuzzy_class_match(None, "Topic") == 0.5


def test_class_match_none_skill():
    assert fuzzy_class_match("Topic", None) == 0.5


# ── fuzzy_token_overlap ────────────────────────────────────────────────────────


def test_token_overlap_full():
    assert fuzzy_token_overlap(["create", "visual"], ["create", "visual", "3d"]) == 1.0


def test_token_overlap_partial():
    score = fuzzy_token_overlap(["create", "visual"], ["create", "audio"])
    assert score == 0.5


def test_token_overlap_none():
    assert fuzzy_token_overlap(["create"], ["audio", "video"]) == 0.0


def test_token_overlap_empty_query():
    assert fuzzy_token_overlap([], ["create", "visual"]) == 0.0


def test_token_overlap_empty_tags():
    assert fuzzy_token_overlap(["create"], []) == 0.0


# ── fuzzy_trust ────────────────────────────────────────────────────────────────


def test_trust_high():
    assert fuzzy_trust("high") == 1.0


def test_trust_medium():
    assert fuzzy_trust("medium") == 0.7


def test_trust_low():
    assert fuzzy_trust("low") == 0.4


def test_trust_unknown():
    assert fuzzy_trust("unknown") == 0.5


# ── parse_template ─────────────────────────────────────────────────────────────


def test_parse_template_basic():
    result = parse_template("skill_class=Process, crud_verb=create, topic=*")
    assert result["skill_class"] == "Process"
    assert result["crud_verb"] == "create"
    assert result["topic"] == "*"


def test_parse_template_fuzzy_prefix():
    result = parse_template("skill_class=~Process")
    assert result["skill_class"] == "~Process"


def test_parse_template_empty():
    assert parse_template("") == {}


# ── Matcher.read_template ──────────────────────────────────────────────────────


def test_read_template_wildcard_matches_all(tmp_path, monkeypatch):
    """Wildcard topic=* should not filter out any skill."""
    from skill_space import store as store_mod

    monkeypatch.setattr(store_mod, "DB_PATH", tmp_path / "space.db")
    from skill_space.store import Store

    s = Store()
    s.upsert_skill(
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

    matcher = Matcher()
    results = matcher.read_template("topic=*")
    assert len(results) >= 1


def test_read_template_no_match(tmp_path, monkeypatch):
    from skill_space import store as store_mod

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
            "fuzzy_tags": "[]",
            "description": "A test skill",
            "last_indexed": "2026-01-01T00:00:00+00:00",
        }
    )

    matcher = Matcher()
    results = matcher.read_template("skill_class=Role")
    # Topic has 0.1 membership in Role — score should be very low but not zero
    assert all(r.final_score <= 0.2 for r in results)
