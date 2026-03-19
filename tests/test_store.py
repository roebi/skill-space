"""Tests for store.py — SQLite upsert and retrieval."""

import pytest

from skill_space import store as store_mod


SAMPLE_SKILL = {
    "name": "brainstorming-topic-en",
    "skill_class": "Topic",
    "crud_verb": None,
    "topic": "brainstorming",
    "requires_role": "creative-mentor",
    "language": "en",
    "repo_url": "https://github.com/roebi/agent-skills",
    "repo_trust": "high",
    "pinned_commit": "a1b2c3d4",
    "fuzzy_tags": '["creative", "ideation"]',
    "description": "A brainstorming skill",
    "last_indexed": "2026-01-01T00:00:00+00:00",
}


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DB_PATH", tmp_path / "space.db")
    from skill_space.store import Store

    return Store()


def test_upsert_returns_id(store):
    skill_id = store.upsert_skill(SAMPLE_SKILL)
    assert isinstance(skill_id, int)
    assert skill_id > 0


def test_upsert_idempotent(store):
    id1 = store.upsert_skill(SAMPLE_SKILL)
    id2 = store.upsert_skill(SAMPLE_SKILL)
    assert id1 == id2


def test_upsert_updates_description(store):
    store.upsert_skill(SAMPLE_SKILL)
    updated = {**SAMPLE_SKILL, "description": "Updated description"}
    store.upsert_skill(updated)
    skills = store.all_skills()
    assert skills[0]["description"] == "Updated description"


def test_all_skills_empty(store):
    assert store.all_skills() == []


def test_all_skills_returns_inserted(store):
    store.upsert_skill(SAMPLE_SKILL)
    skills = store.all_skills()
    assert len(skills) == 1
    assert skills[0]["name"] == "brainstorming-topic-en"


def test_all_skills_multiple(store):
    store.upsert_skill(SAMPLE_SKILL)
    second = {**SAMPLE_SKILL, "name": "second-skill-en", "topic": "testing"}
    store.upsert_skill(second)
    assert len(store.all_skills()) == 2


def test_skill_fields_preserved(store):
    store.upsert_skill(SAMPLE_SKILL)
    skill = store.all_skills()[0]
    assert skill["skill_class"] == "Topic"
    assert skill["topic"] == "brainstorming"
    assert skill["repo_trust"] == "high"
    assert skill["pinned_commit"] == "a1b2c3d4"
