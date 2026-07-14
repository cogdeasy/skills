# Contributing

Thanks for contributing to the ElevenLabs skills library! This guide covers how to
author a skill, validate it, and run the evals.

## Repository layout

```
<skill-name>/            # one directory per skill
  SKILL.md               # the skill itself (frontmatter + instructions)
  references/            # optional supporting docs linked from SKILL.md
evals/
  run_all.py             # eval harness (drives the Cursor Agent CLI)
  validate_skills.py     # frontmatter / eval-config validator
  <skill-name>/
    evals.json           # functional evals (prompt + expectations)
    trigger_eval.json    # trigger evals (query + should_trigger)
tests/                   # pytest suite for the validator and harness utilities
```

## Authoring a skill

Skills follow the [Agent Skills specification](https://agentskills.io/specification).
Create a new top-level directory containing a `SKILL.md` that starts with YAML
frontmatter:

```markdown
---
name: my-skill                  # must match the directory name; lowercase + hyphens
description: What it does. Use when ...   # <=1024 chars; drives skill triggering
license: MIT
compatibility: Requires internet access and an ElevenLabs API key (ELEVENLABS_API_KEY).
metadata: {"openclaw": {"requires": {"env": ["ELEVENLABS_API_KEY"]}, "primaryEnv": "ELEVENLABS_API_KEY"}}
---

# My Skill

Instructions for the agent...
```

Guidelines:

- The `description` is what makes a skill trigger — include both *what it does* and
  *when to use it*.
- Put longer supporting material in `references/` and link it with relative links
  (the validator checks that these links resolve).
- JavaScript examples must use `@elevenlabs/elevenlabs-js`, never the deprecated
  `elevenlabs` v1 npm package.
- Add the skill to `ALL_SKILLS` in `evals/run_all.py`, create
  `evals/<skill-name>/evals.json` and `evals/<skill-name>/trigger_eval.json`, and
  list the skill in the README table.
- Record the change in `CHANGELOG.md`.

## Validating

```bash
# Frontmatter + eval-config validation (no dependencies beyond Python 3.10+)
python3 evals/validate_skills.py

# Harness dry run (validates everything the evals need, without cursor-agent)
python3 evals/run_all.py --dry-run

# Lint and tests
pip install ruff pytest
ruff check evals tests
pytest
```

All of the above run in CI on every pull request.

## Running evals

Full evals require the [Cursor Agent CLI](https://cursor.com/docs/cli/using)
(`cursor-agent`) on your PATH. They exercise real model calls, so expect them to
take several minutes.

```bash
# Everything (trigger + functional)
python3 evals/run_all.py -v

# Trigger evals only (~3 min) — do the right queries fire the skill?
python3 evals/run_all.py --trigger-only -v

# Functional evals only (~15 min) — does the skill produce correct output?
python3 evals/run_all.py --functional-only -v

# A single skill
python3 evals/run_all.py --skills my-skill -v
```

Results are written to `evals/results/<timestamp>/` (gitignored) with a
`report.md` summary.

## Pull requests

- Keep PRs focused: one skill or one harness change per PR.
- Make sure `python3 evals/validate_skills.py`, `ruff check evals tests`, and
  `pytest` pass locally before opening the PR.
- Update `CHANGELOG.md` under `[Unreleased]`.
