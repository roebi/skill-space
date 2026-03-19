"""skill-space CLI — Fuzzy Tuple Space for Agent Skills."""

import typer
from rich.console import Console

app = typer.Typer(
    name="skill-space",
    help="Fuzzy Tuple Space for Agent Skills. Index repos, search by fuzzy template, track learning.",
    no_args_is_help=True,
)
console = Console()


# ── Sub-command groups ─────────────────────────────────────────────────────────

index_app = typer.Typer(help="Index skill git repos into the local space.")
search_app = typer.Typer(help="Search and match skills.")
learn_app = typer.Typer(help="Learning journal: claim, done, next.")
space_app = typer.Typer(help="Space health: stats, drift.")

app.add_typer(index_app, name="index")
app.add_typer(search_app, name="search")
app.add_typer(learn_app, name="learn")
app.add_typer(space_app, name="space")


# ── index ──────────────────────────────────────────────────────────────────────


@index_app.command("run")
def index_run(
    repo: str = typer.Option(None, help="Single repo URL to index (overrides config)."),
    force: bool = typer.Option(False, "--force", help="Re-index even if up to date."),
) -> None:
    """Crawl configured repos, parse SKILL.md files, embed and store."""
    from skill_space.indexer import Indexer

    indexer = Indexer()
    indexer.run(repo_url=repo, force=force)


# ── search ─────────────────────────────────────────────────────────────────────


@search_app.command("query")
def search_query(
    query: str = typer.Argument(
        ..., help="Free-text query, e.g. 'create something visual with 3d'"
    ),
    skill_class: str = typer.Option(
        None, "--class", help="Filter: Role | Topic | Process | OneStepProcess"
    ),
    lang: str = typer.Option("en", "--lang", help="Language filter."),
    top: int = typer.Option(5, "--top", help="Number of results."),
) -> None:
    """Semantic + fuzzy search across all indexed skills."""
    from skill_space.matcher import Matcher

    matcher = Matcher()
    results = matcher.search(query=query, skill_class=skill_class, lang=lang, top=top)
    from skill_space.display import display_results

    display_results(results)


@search_app.command("read")
def search_read(
    template: str = typer.Argument(
        ...,
        help="Linda-style template, e.g. 'skill_class=Process, crud_verb=create, topic=*'",
    ),
) -> None:
    """Template-based tuple matching (JavaSpaces / Linda style)."""
    from skill_space.matcher import Matcher

    matcher = Matcher()
    results = matcher.read_template(template)
    from skill_space.display import display_results

    display_results(results)


# ── learn ──────────────────────────────────────────────────────────────────────


@learn_app.command("claim")
def learn_claim(skill_name: str = typer.Argument(...)) -> None:
    """Mark a skill as 'currently learning'."""
    from skill_space.journal import Journal

    Journal().claim(skill_name)
    console.print(f"[green]Claimed:[/green] {skill_name}")


@learn_app.command("done")
def learn_done(
    skill_name: str = typer.Argument(...),
    level: int = typer.Option(..., "--level", min=1, max=5, help="Mastery level reached (1–5)."),
) -> None:
    """Record completion of a skill at a given mastery level."""
    from skill_space.journal import Journal

    Journal().done(skill_name, level=level)
    console.print(f"[green]Done:[/green] {skill_name} at level {level}")


@learn_app.command("next")
def learn_next(
    topic: str = typer.Option(None, "--topic", help="Filter suggestions by topic."),
) -> None:
    """Predict the best next skill to learn based on your journal."""
    from skill_space.predictor import Predictor

    suggestion = Predictor().next_skill(topic=topic)
    from skill_space.display import display_suggestion

    display_suggestion(suggestion)


# ── space ──────────────────────────────────────────────────────────────────────


@space_app.command("stats")
def space_stats() -> None:
    """Show space statistics: repos indexed, skill count, last sync."""
    from skill_space.store import Store

    Store().print_stats()


@space_app.command("drift")
def space_drift() -> None:
    """Detect stale skills: pinned commits behind HEAD, old last-touched dates."""
    from skill_space.indexer import Indexer

    Indexer().drift_report()


if __name__ == "__main__":
    app()
