"""Display — rich terminal output for search results and suggestions."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.table import Table

from skill_space.matcher import SkillMatch

console = Console()


def display_results(results: list[SkillMatch]) -> None:
    if not results:
        console.print("[yellow]No matches found.[/yellow]")
        return

    t = Table(title="Skill Space Results")
    t.add_column("Score", style="cyan", width=6)
    t.add_column("Skill Name", style="bold")
    t.add_column("Class", width=14)
    t.add_column("Topic", width=16)
    t.add_column("Why", style="dim")

    for r in results:
        s = r.skill
        t.add_row(
            f"{r.final_score:.2f}",
            s["name"],
            s.get("skill_class") or "?",
            s.get("topic") or "?",
            ", ".join(r.reasons),
        )
    console.print(t)


def display_suggestion(suggestion: Optional[SkillMatch]) -> None:
    if suggestion is None:
        console.print("[yellow]No suggestion available — index more skills or complete more learning events.[/yellow]")
        return

    s = suggestion.skill
    console.print(f"\n[bold green]Suggested next skill:[/bold green] {s['name']}")
    console.print(f"  Class:    {s.get('skill_class', '?')}")
    console.print(f"  Topic:    {s.get('topic', '?')}")
    console.print(f"  Score:    {suggestion.final_score:.2f}")
    console.print(f"  Reasons:  {', '.join(suggestion.reasons)}")
    console.print(f"  Repo:     {s.get('repo_url', '?')}\n")
