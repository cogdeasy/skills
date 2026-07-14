# Changelog

All notable changes to the skills in this repository are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Entries cover changes to the skill packages (`*/SKILL.md` and their `references/`)
and the eval harness under `evals/`.

## [Unreleased]

### Added
- CI pipeline (`.github/workflows/ci.yml`): SKILL.md frontmatter validation, eval
  harness dry run, ruff lint, and the pytest suite.
- Scheduled upstream drift check (`.github/workflows/upstream-sync-check.yml`) that
  opens/updates an issue when this fork falls behind `elevenlabs/skills`, including
  detection of skills removed upstream but still present in the fork.
- `evals/validate_skills.py`: standalone frontmatter and eval-config validator.
- `--dry-run` mode for `evals/run_all.py` (validates skills and eval configs without
  invoking cursor-agent).
- Unit and integration test suite under `tests/`.
- `CONTRIBUTING.md` with skill-authoring and eval documentation.

## 2026-07-06

### Changed
- Weekly skills update from the ElevenLabs changelog (upstream PR #98).

## Earlier history

For changes prior to this file's introduction, see the git history of
[elevenlabs/skills](https://github.com/elevenlabs/skills/commits/main).
