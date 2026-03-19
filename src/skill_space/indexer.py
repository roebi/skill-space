"""Indexer — crawl skill git repos, parse SKILL.md, embed, store."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console

from skill_space.store import Store

console = Console()
CONFIG_PATH = Path.home() / ".skill-space" / "config.toml"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"repos": []}
    import tomllib  # py 3.11+

    return tomllib.loads(CONFIG_PATH.read_text())


def _parse_skill_md(path: Path) -> Optional[dict]:
    """Parse frontmatter from a SKILL.md file."""
    text = path.read_text(errors="replace")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    # Extract body description (first non-empty line after frontmatter)
    body = text[match.end() :].strip()
    first_para = body.split("\n\n")[0].strip().lstrip("#").strip()
    return {
        "name": fm.get("name", path.parent.name),
        "skill_class": fm.get("metadata", {}).get("skill-class")
        if isinstance(fm.get("metadata"), dict)
        else None,
        "crud_verb": fm.get("metadata", {}).get("crud-verb")
        if isinstance(fm.get("metadata"), dict)
        else None,
        "topic": fm.get("metadata", {}).get("topic")
        if isinstance(fm.get("metadata"), dict)
        else None,
        "requires_role": fm.get("metadata", {}).get("requires-role")
        if isinstance(fm.get("metadata"), dict)
        else None,
        "language": "en"
        if path.parent.name.endswith("-en")
        else fm.get("metadata", {}).get("lang", "en")
        if isinstance(fm.get("metadata"), dict)
        else "en",
        "description": first_para,
        "fuzzy_tags": json.dumps(_extract_tags(fm, body)),
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }


def _extract_tags(fm: dict, body: str) -> list[str]:
    """Lightweight tag extraction from frontmatter + body keywords."""
    tags: set[str] = set()
    desc = str(fm.get("description", ""))
    for word in re.findall(r"\b[a-z][a-z0-9\-]{3,}\b", (desc + " " + body).lower()):
        if word not in {"this", "that", "with", "from", "when", "skill", "user", "agent"}:
            tags.add(word)
    return sorted(tags)[:30]  # cap at 30


class Indexer:
    def __init__(self) -> None:
        self.store = Store()

    def run(self, repo_url: Optional[str] = None, force: bool = False) -> None:
        config = _load_config()
        repos = [{"url": repo_url, "trust": "high"}] if repo_url else config.get("repos", [])

        if not repos:
            console.print(
                "[yellow]No repos configured. Add repos to ~/.skill-space/config.toml[/yellow]"
            )
            return

        for repo_conf in repos:
            self._index_repo(repo_conf, force=force)

    def _index_repo(self, repo_conf: dict, force: bool) -> None:
        import tempfile
        import git  # gitpython

        url = repo_conf["url"]
        trust = repo_conf.get("trust", "high")
        console.print(f"[cyan]Indexing[/cyan] {url} (trust={trust})")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                grepo = git.Repo.clone_from(url, tmpdir, depth=1)
                commit = grepo.head.commit.hexsha[:8]
            except Exception as e:
                console.print(f"[red]Clone failed:[/red] {e}")
                return

            skills_dir = Path(tmpdir) / "skills"
            if not skills_dir.exists():
                skills_dir = Path(tmpdir)

            count = 0
            for skill_md in skills_dir.rglob("SKILL.md"):
                parsed = _parse_skill_md(skill_md)
                if not parsed:
                    continue
                parsed["repo_url"] = url
                parsed["repo_trust"] = trust
                parsed["pinned_commit"] = commit
                skill_id = self.store.upsert_skill(parsed)
                self._embed_and_store(skill_id, parsed)
                count += 1

        console.print(f"  [green]✓[/green] {count} skills indexed")

    def _embed_and_store(self, skill_id: int, parsed: dict) -> None:
        try:
            from skill_space.embedder import Embedder

            text = f"{parsed['name']} {parsed.get('topic', '')} {parsed.get('description', '')}"
            vec = Embedder().encode(text)
            self.store.store_embedding(skill_id, vec)
        except Exception:
            pass  # embeddings optional — fuzzy-only fallback still works

    def drift_report(self) -> None:
        from rich.table import Table

        skills = self.store.all_skills()
        t = Table(title="Drift Report — Potentially Stale Skills")
        t.add_column("Skill")
        t.add_column("Pinned Commit")
        t.add_column("Last Indexed")
        t.add_column("Repo Trust")
        for s in skills:
            t.add_row(
                s["name"],
                s.get("pinned_commit", "?"),
                s.get("last_indexed", "?")[:10],
                s.get("repo_trust", "?"),
            )
        Console().print(t)
