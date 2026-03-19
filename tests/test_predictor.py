"""Tests for predictor.py — readiness scoring and next_skill suggestion."""

import pytest

from skill_space import store as store_mod

TOPIC_SKILL = {
    "name": "brainstorming-topic-en",
    "skill_class": "Topic",
    "crud_verb": None,
    "topic": "brainstorming",
    "requires_role": None,
    "language": "en",
    "repo_url": "https://github.com/roebi/agent-skills",
    "repo_trust": "high",
    "pinned_commit": "abc123",
    "fuzzy_tags": '["creative"]',
    "description": "Brainstorming topic skill",
    "last_indexed": "2026-01-01T00:00:00+00:00",
}

PROCESS_SKILL = {
    "name": "create-skill-process-en",
    "skill_class": "Process",
    "crud_verb": "create",
    "topic": "skill",
    "requires_role": "skill-author",
    "language": "en",
    "repo_url": "https://github.com/roebi/agent-skills",
    "repo_trust": "high",
    "pinned_commit": "def456",
    "fuzzy_tags": '["create", "skill"]',
    "description": "Create skill process",
    "last_indexed": "2026-01-01T00:00:00+00:00",
}

ROLE_SKILL = {
    "name": "role-skill-author-en",
    "skill_class": "Role",
    "crud_verb": None,
    "topic": "skill-author",
    "requires_role": None,
    "language": "en",
    "repo_url": "https://github.com/roebi/agent-skills",
    "repo_trust": "high",
    "pinned_commit": "ghi789",
    "fuzzy_tags": '["role", "author"]',
    "description": "Skill author role",
    "last_indexed": "2026-01-01T00:00:00+00:00",
}


@pytest.fixture()
def predictor(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DB_PATH", tmp_path / "space.db")
    from skill_space.predictor import Predictor

    return Predictor()


def test_next_skill_empty_space(predictor):
    assert predictor.next_skill() is None


def test_next_skill_returns_something(predictor):
    predictor.store.upsert_skill(TOPIC_SKILL)
    result = predictor.next_skill()
    assert result is not None
    assert result.skill["name"] == "brainstorming-topic-en"


def test_next_skill_excludes_completed(predictor):
    predictor.store.upsert_skill(TOPIC_SKILL)
    predictor.journal.done("brainstorming-topic-en", level=5)
    assert predictor.next_skill() is None


def test_next_skill_topic_filter(predictor):
    predictor.store.upsert_skill(TOPIC_SKILL)
    predictor.store.upsert_skill(PROCESS_SKILL)
    result = predictor.next_skill(topic="brainstorming")
    assert result is not None
    assert result.skill["name"] == "brainstorming-topic-en"


def test_readiness_boosted_when_role_done(predictor):
    predictor.store.upsert_skill(PROCESS_SKILL)
    # Without role done
    score_before = predictor._readiness(PROCESS_SKILL, completed=set())
    # With role done
    score_after = predictor._readiness(PROCESS_SKILL, completed={"role-skill-author-en"})
    assert score_after > score_before


def test_readiness_penalised_when_role_missing(predictor):
    predictor.store.upsert_skill(PROCESS_SKILL)
    score = predictor._readiness(PROCESS_SKILL, completed=set())
    assert score < 0.5


def test_readiness_neutral_no_requires_role(predictor):
    score = predictor._readiness(TOPIC_SKILL, completed=set())
    assert score == 0.5


def test_next_skill_score_between_zero_and_one(predictor):
    predictor.store.upsert_skill(TOPIC_SKILL)
    result = predictor.next_skill()
    assert 0.0 <= result.final_score <= 1.0
