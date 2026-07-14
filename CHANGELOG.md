# Changelog

All notable changes to the skills in this repository are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Entries cover changes to the skill packages (`*/SKILL.md` and their `references/`)
and the eval harness under `evals/`.

Sections up to and including 2026-07-08 were reconstructed retroactively from the
git history of [elevenlabs/skills](https://github.com/elevenlabs/skills/commits/main).

## [Unreleased]

### Added
- Automated upstream-sync PRs: the drift-check workflow now merges
  `upstream/main` into an `upstream-sync` branch and opens/updates a PR
  (flagging any merge conflicts in the PR body) instead of only filing an issue
  (`.github/workflows/upstream-sync-check.yml`, `scripts/upstream_sync_pr.py`).
- Historical changelog backfill for all nine skills (this file).
- CI pipeline (`.github/workflows/ci.yml`): SKILL.md frontmatter validation, eval
  harness dry run, ruff lint, and the pytest suite.
- Scheduled upstream drift check (`.github/workflows/upstream-sync-check.yml`)
  against `elevenlabs/skills`, including detection of skills removed upstream but
  still present in the fork.
- `evals/validate_skills.py`: standalone frontmatter and eval-config validator.
- `--dry-run` mode for `evals/run_all.py` (validates skills and eval configs without
  invoking cursor-agent).
- Unit and integration test suite under `tests/`.
- `CONTRIBUTING.md` with skill-authoring and eval documentation.

## 2026-07-08

### Changed
- **agents**, **music**: weekly skills update from the ElevenLabs changelog of
  2026-07-06 (upstream PR #98).

## 2026-07-01

### Added
- **speech-engine**: `disableAuth` parameter documented (upstream PR #95).

## 2026-06-30

### Changed
- **agents**, **music** (indirectly), **speech-to-text**, **text-to-speech**:
  weekly skills update from the ElevenLabs changelog of 2026-06-29 (upstream
  PR #94).

## 2026-06-23

### Changed
- **agents**, **music**, **speech-to-text**: weekly skills update from the
  changelog of 2026-06-22; removed an overly narrow client-tool schema detail
  from the agents skill (upstream PR #91).

## 2026-06-16

### Changed
- **agents**, **music**, **speech-to-text**: weekly skills update from the
  changelog of 2026-06-15; documented conversation evaluation reruns in the
  agents skill (upstream PRs #85, #89).

## 2026-06-15

### Changed
- **music**: updated the skill for the Music v2 API, ignoring v1-only
  parameters when v2 is used (upstream PR #87).

## 2026-06-10

### Added
- **agents**: documented widget launcher modes.

### Changed
- **agents**: skills update from the changelog of 2026-06-08.
- **setup-api-key**: clarified API-key source precedence and the skill's
  relevance filter; fixed its eval workflow expectation (upstream PR #84 —
  the skill was briefly removed on 2026-06-08 and restored on 2026-06-09).

## 2026-06-02

### Changed
- **agents**, **music**, **speech-to-text**: skills updates from the changelogs
  of 2026-05-25 and 2026-06-01; trimmed `text_behavior_overrides` docs to match
  the agents create API reference; separated video-to-music from the compose
  API in the music docs (upstream PRs #80–#82).

## 2026-05-20

### Changed
- **speech-engine**: documented overrides and WSS transport (upstream PR #71).

## 2026-05-14 – 2026-05-15

### Added
- **speech-engine**: new skill — real-time voice conversations for custom LLMs,
  with Python and JavaScript SDK references, standalone-server example, LiveKit
  override, and `speechEngineId` configuration (upstream PRs #63, #68, #69).

### Changed
- **agents**, **setup-api-key**: skills update from the 2026-05-13 brief;
  pinned the LiveKit version (upstream PRs #66, #67).

## 2026-05-09 – 2026-05-13

### Changed
- **agents**: skills update from the 2026-05-04 brief; removed a duplicate tags
  example (upstream PR #61).
- **evals**: fixed trigger evals and deprecated-import detection; made the
  harness cursor-specific (upstream PRs #61, #62).

## 2026-05-01 – 2026-05-07

### Added
- **agents**: workflows, guardrails, testing, and tool-reference sections.

### Changed
- **agents**, **speech-to-text**: skills update from the changelog of
  2026-04-27; LLM tables scoped to the skills brief.
- **voice-changer**: SKILL.md update.

## 2026-04-20 – 2026-04-22

### Added
- **voice-changer**: new skill — speech-to-speech voice transformation, with
  working evals.
- **voice-isolator**: new skill — background-noise removal and vocal isolation.

### Changed
- **agents**, **speech-to-text**: skills update from the 2026-04-20 brief.

## 2026-04-02 – 2026-04-13

### Changed
- **agents**, **music**, **speech-to-text**: skills docs updates for the
  2026-04-01, 2026-04-07, and 2026-04-13 briefs; agents updated for the latest
  APIs.

## 2026-03-04 – 2026-03-23

### Added
- **setup-api-key**: API-key environment check (upstream PR #12).

### Changed
- **agents**: documented environment-aware tools and content guardrails;
  removed coaching settings; docs updates for the 2026-02-23, 2026-03-02, and
  2026-03-16 briefs.
- **music**, **speech-to-text**: skills docs updates for the 2026-03-02 and
  2026-03-09 changelogs.

## 2026-02-26

### Changed
- **speech-to-text**: documented transcription statuses and explicit VAD
  behavior.

## 2026-02-02 – 2026-02-20

### Added
- **agents**: outbound-calls reference.
- All skills: `metadata` frontmatter for OpenClaw.

### Changed
- All skills: description updates and a broad round of fixes ("lots of fixes",
  2026-02-20); agents parameters corrected; skills update from the changelog of
  2026-02-09.

## 2026-01-24 – 2026-01-29

### Added
- Initial skill library: **text-to-speech**, **speech-to-text**, **agents**
  (renamed from `conversational-ai`), **music**, **sound-effects**, and
  **setup-api-key**, plus the shared installation guide, realtime STT and
  websocket TTS references, repo logo, and README.
- License and compatibility frontmatter for every skill.

### Changed
- Markdown formatting cleanup, updated models/API usage, references moved back
  into per-skill folders, and outdated exception handling removed.
