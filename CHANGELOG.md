# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-03-19

### Fixed
- Indexer now reads `description` from frontmatter field directly (was reading first body paragraph, missing the actual skill description)
- Metadata parsing simplified — handles missing or non-dict `metadata` block gracefully
- Language detection extended to `-de` suffix skills

## [0.2.0] - 2026-03-19

### Changed
- `sentence-transformers` is now an **optional** dependency (fixes [#1](https://github.com/roebi/skill-space/issues/1))
  - Default install is lightweight, pure Python, no PyTorch/CUDA
  - Opt in with `pip install "skill-tuple-space[semantic]"`
  - Fuzzy matching works fully without semantic layer

### Added
- Project URLs in `pyproject.toml` (Homepage, Repository, Issues) for PyPI verification

## [0.1.0] - 2026-03-19

### Added
- Initial release
- Fuzzy Tuple Space for Agent Skills inspired by Linda / JavaSpaces
- `skill-space index` — crawl skill git repos and index SKILL.md files
- `skill-space search query` — fuzzy + semantic search
- `skill-space search read` — Linda-style tuple template matching
- `skill-space learn` — claim, done, next (learning journal + predictor)
- `skill-space space` — stats and drift detection
- Multi-repo federation with configurable trust levels
