"""Predictor — combines fuzzy matching + learning journal to suggest next skill."""

from __future__ import annotations

from typing import Optional

from skill_space.journal import Journal
from skill_space.matcher import Matcher, SkillMatch, fuzzy_class_match, fuzzy_trust
from skill_space.store import Store


class Predictor:
    def __init__(self) -> None:
        self.journal = Journal()
        self.store = Store()
        self.matcher = Matcher()

    def next_skill(self, topic: Optional[str] = None) -> Optional[SkillMatch]:
        completed = self.journal.completed_names()
        skills = self.store.all_skills()

        candidates: list[SkillMatch] = []
        for s in skills:
            if s["name"] in completed:
                continue
            if topic and topic.lower() not in (s.get("topic") or "").lower():
                continue

            readiness = self._readiness(s, completed)
            trust = fuzzy_trust(s.get("repo_trust", "high"))
            final = readiness * 0.7 + trust * 0.3

            candidates.append(
                SkillMatch(
                    skill=s,
                    fuzzy_score=readiness,
                    final_score=final,
                    reasons=[f"readiness~{readiness:.2f}", f"trust~{trust:.2f}"],
                )
            )

        candidates.sort(key=lambda c: c.final_score, reverse=True)
        return candidates[0] if candidates else None

    def _readiness(self, skill: dict, completed: set[str]) -> float:
        """
        Heuristic readiness score:
        - If skill has requires_role and that role-skill is not yet done → penalise
        - If skill_class is Process and user has done at least 2 Topic-class skills → boost
        - Otherwise neutral
        """
        score = 0.5

        req_role = skill.get("requires_role")
        if req_role:
            role_done = any(req_role in name for name in completed)
            score += 0.3 if role_done else -0.2

        skill_class = skill.get("skill_class", "")
        if skill_class == "Process":
            topic_done_count = sum(
                1 for name in completed
                if self._class_of(name) == "Topic"
            )
            score += min(topic_done_count * 0.05, 0.2)

        return max(0.0, min(1.0, score))

    def _class_of(self, skill_name: str) -> Optional[str]:
        all_skills = {s["name"]: s for s in self.store.all_skills()}
        return all_skills.get(skill_name, {}).get("skill_class")
