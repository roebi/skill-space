# skill-tuple-space

**Fuzzy Tuple Space for Agent Skills.**

Inspired by David Gelernter's Linda coordination language and JavaSpaces,
`skill-tuple-space` indexes your agent skill git repos into a local SQLite store
and lets you query them using two complementary mechanisms:

- **Fuzzy layer** — membership-function scoring on structured metadata
  (`skill_class`, `crud_verb`, `topic`, `requires_role`).
- **Semantic layer** — RAG / cosine similarity on SKILL.md descriptions
  via `sentence-transformers`.

These are **two distinct things**: the semantic layer finds what is _similar_,
the fuzzy layer reasons about how well something _fits your current taxonomy and context_.

## Install

```bash
uv pip install -e ".[dev]"
```

## Quickstart

```bash
# 1. Copy and edit config
mkdir -p ~/.skill-space
cp config.example.toml ~/.skill-space/config.toml

# 2. Index your repos
skill-space index run

# 3. Semantic + fuzzy search
skill-space search query "create something visual with 3d"

# 4. Linda-style template matching
skill-space search read "skill_class=Process, crud_verb=create, topic=*"

# 5. Learning journal
skill-space learn claim create-openscad-from-construction-image-en
skill-space learn done create-openscad-from-construction-image-en --level 4
skill-space learn next --topic agent-skills

# 6. Space health
skill-space space stats
skill-space space drift
```

## Architecture

```
src/skill_space/
├── cli.py        # typer CLI entry point
├── indexer.py    # git clone + SKILL.md parse + embed
├── embedder.py   # sentence-transformers (all-MiniLM-L6-v2, 384-dim)
├── store.py      # SQLite + sqlite-vec persistence
├── matcher.py    # fuzzy membership functions + cosine combiner
├── journal.py    # learning events CRUD
├── predictor.py  # readiness scoring + next-skill suggestion
└── display.py    # rich terminal output
```

## License

MIT
