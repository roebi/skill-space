"""Matcher — fuzzy metadata scoring + semantic RAG, combined.

Two distinct layers:
  1. FuzzyMatcher  — operates on structured metadata fields (skill_class, crud_verb,
                     topic, requires_role).  Uses membership functions, not cosine.
  2. SemanticMatcher — cosine similarity on description embeddings (RAG layer).

Final score = w_fuzzy * fuzzy_score + w_semantic * semantic_score
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

from skill_space.store import Store


# ── Fuzzy membership functions ─────────────────────────────────────────────────

# Skill class hierarchy — partial membership across adjacent classes
_CLASS_MEMBERSHIP: dict[str, dict[str, float]] = {
    "OneStepProcess": {"OneStepProcess": 1.0, "Process": 0.7, "Topic": 0.1, "Role": 0.0},
    "Process":        {"Process": 1.0, "OneStepProcess": 0.6, "Topic": 0.2, "Role": 0.0},
    "Topic":          {"Topic": 1.0, "Process": 0.3, "Role": 0.1, "OneStepProcess": 0.2},
    "Role":           {"Role": 1.0, "Topic": 0.1, "Process": 0.0, "OneStepProcess": 0.0},
}


def fuzzy_class_match(query_class: Optional[str], skill_class: Optional[str]) -> float:
    """Degree to which skill_class satisfies query_class."""
    if query_class is None or skill_class is None:
        return 0.5  # unknown → neutral, not zero
    return _CLASS_MEMBERSHIP.get(skill_class, {}).get(query_class, 0.0)


def fuzzy_token_overlap(query_tokens: list[str], skill_tags: list[str]) -> float:
    """Jaccard-ish overlap between query tokens and skill fuzzy_tags."""
    if not query_tokens or not skill_tags:
        return 0.0
    hits = sum(1 for t in query_tokens if any(t in tag or tag in t for tag in skill_tags))
    return hits / len(query_tokens)


def fuzzy_trust(trust: str) -> float:
    return {"high": 1.0, "medium": 0.7, "low": 0.4}.get(trust, 0.5)


# ── Template parser (Linda-style) ──────────────────────────────────────────────

def parse_template(template: str) -> dict:
    """
    Parse 'skill_class=Process, crud_verb=create, topic=*' into a dict.
    '*' means wildcard (no filter).  '~Process' means fuzzy match.
    """
    result: dict[str, str] = {}
    for part in re.split(r",\s*", template):
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class SkillMatch:
    skill: dict
    fuzzy_score: float = 0.0
    semantic_score: float = 0.0
    final_score: float = 0.0
    reasons: list[str] = field(default_factory=list)


# ── Matcher ────────────────────────────────────────────────────────────────────

W_FUZZY = 0.45
W_SEMANTIC = 0.55


class Matcher:
    def __init__(self) -> None:
        self.store = Store()

    def search(
        self,
        query: str,
        skill_class: Optional[str] = None,
        lang: str = "en",
        top: int = 5,
    ) -> list[SkillMatch]:
        skills = self.store.all_skills()
        query_tokens = re.findall(r"\b[a-z]{3,}\b", query.lower())

        # Semantic embedding for the query
        sem_scores: dict[str, float] = {}
        try:
            from skill_space.embedder import Embedder
            q_vec = Embedder().encode(query)
            sem_scores = self._cosine_all(q_vec, skills)
        except Exception:
            pass

        results: list[SkillMatch] = []
        for s in skills:
            if lang and s.get("language") != lang:
                continue

            tags = json.loads(s.get("fuzzy_tags") or "[]")

            # Fuzzy layer
            class_score = fuzzy_class_match(skill_class, s.get("skill_class"))
            tag_score = fuzzy_token_overlap(query_tokens, tags)
            trust_score = fuzzy_trust(s.get("repo_trust", "high"))
            fuzzy = (class_score * 0.4 + tag_score * 0.5 + trust_score * 0.1)

            # Semantic layer
            semantic = sem_scores.get(s["name"], 0.0)

            final = W_FUZZY * fuzzy + W_SEMANTIC * semantic

            reasons: list[str] = []
            if class_score > 0.5:
                reasons.append(f"class~{class_score:.2f}")
            if tag_score > 0.3:
                reasons.append(f"tags~{tag_score:.2f}")
            if semantic > 0.4:
                reasons.append(f"semantic~{semantic:.2f}")

            results.append(SkillMatch(s, fuzzy, semantic, final, reasons))

        results.sort(key=lambda r: r.final_score, reverse=True)
        return results[:top]

    def read_template(self, template: str) -> list[SkillMatch]:
        """Linda-style template match with fuzzy class membership."""
        tmpl = parse_template(template)
        skills = self.store.all_skills()
        results: list[SkillMatch] = []

        for s in skills:
            score = 1.0
            reasons: list[str] = []
            for field_name, value in tmpl.items():
                if value == "*":
                    continue
                fuzzy = value.startswith("~")
                v = value.lstrip("~")
                skill_val = s.get(field_name, "")

                if field_name == "skill_class":
                    m = fuzzy_class_match(v, skill_val)
                else:
                    m = 1.0 if skill_val == v else (0.5 if v.lower() in str(skill_val).lower() else 0.0)

                score *= m
                reasons.append(f"{field_name}={m:.2f}")

            if score > 0.0:
                results.append(SkillMatch(s, fuzzy_score=score, final_score=score, reasons=reasons))

        results.sort(key=lambda r: r.final_score, reverse=True)
        return results[:10]

    def _cosine_all(self, q_vec: list[float], skills: list[dict]) -> dict[str, float]:
        import numpy as np
        from skill_space.embedder import Embedder
        emb = Embedder()
        scores: dict[str, float] = {}
        q = np.array(q_vec)
        for s in skills:
            text = f"{s['name']} {s.get('topic', '')} {s.get('description', '')}"
            v = np.array(emb.encode(text))
            cos = float(np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-9))
            scores[s["name"]] = cos
        return scores
