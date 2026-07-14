#!/usr/bin/env python3
"""Validate SKILL.md frontmatter and eval configs for all skills in the repo.

Checks, per skill directory:
  - SKILL.md exists and starts with YAML frontmatter delimited by `---` lines
  - required fields: name, description
  - name matches the skill directory name and follows the Agent Skills
    specification (lowercase letters, digits, hyphens; max 64 chars)
  - description is non-empty and at most 1024 characters
  - metadata field, when present, is valid JSON
  - relative markdown links in SKILL.md resolve to files that exist
  - evals/<skill>/evals.json and evals/<skill>/trigger_eval.json (when present)
    are valid JSON with the expected shape

Usage:
    python3 evals/validate_skills.py            # validate all skills
    python3 evals/validate_skills.py tts music  # validate specific skills

Exits non-zero if any validation error is found.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EVALS_DIR = Path(__file__).parent

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
KNOWN_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools", "version"}


def discover_skill_dirs(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Return all top-level skill directories (those containing a SKILL.md)."""
    return sorted(
        p for p in repo_root.iterdir()
        if p.is_dir() and not p.name.startswith(".") and (p / "SKILL.md").exists()
    )


def parse_frontmatter(content: str) -> dict[str, str]:
    """Parse simple `key: value` YAML frontmatter from SKILL.md content.

    Raises ValueError if the frontmatter block is missing or malformed.
    """
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing frontmatter: file must start with '---'")
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("missing closing '---' for frontmatter")

    fields: dict[str, str] = {}
    fm_lines = lines[1:end_idx]
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if not match:
            raise ValueError("malformed frontmatter line: %r" % line)
        key = match.group(1)
        value = match.group(2).strip()
        if value in (">", "|", ">-", "|-"):
            parts = []
            i += 1
            while i < len(fm_lines) and (fm_lines[i].startswith("  ") or fm_lines[i].startswith("\t")):
                parts.append(fm_lines[i].strip())
                i += 1
            fields[key] = " ".join(parts)
            continue
        fields[key] = value.strip().strip('"').strip("'")
        i += 1
    return fields


def validate_frontmatter(fields: dict[str, str], skill_dir_name: str) -> list[str]:
    """Return a list of validation error strings for parsed frontmatter fields."""
    errors: list[str] = []

    name = fields.get("name", "")
    if not name:
        errors.append("missing required field: name")
    else:
        if name != skill_dir_name:
            errors.append("name %r does not match directory name %r" % (name, skill_dir_name))
        if len(name) > MAX_NAME_LENGTH:
            errors.append("name exceeds %d characters" % MAX_NAME_LENGTH)
        if not NAME_RE.match(name):
            errors.append("name %r must be lowercase letters, digits, and hyphens" % name)

    description = fields.get("description", "")
    if not description:
        errors.append("missing required field: description")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append("description exceeds %d characters" % MAX_DESCRIPTION_LENGTH)

    metadata = fields.get("metadata")
    if metadata:
        try:
            json.loads(metadata)
        except json.JSONDecodeError as exc:
            errors.append("metadata is not valid JSON: %s" % exc)

    for key in fields:
        if key not in KNOWN_FIELDS:
            errors.append("unknown frontmatter field: %s" % key)

    return errors


RELATIVE_LINK_RE = re.compile(r"\]\((?!https?://|mailto:|#)([^)\s]+)\)")


def validate_relative_links(content: str, skill_dir: Path) -> list[str]:
    """Check that relative markdown links in SKILL.md resolve to existing files."""
    errors: list[str] = []
    for match in RELATIVE_LINK_RE.finditer(content):
        target = match.group(1).split("#")[0]
        if not target:
            continue
        if target.startswith("/"):
            resolved = REPO_ROOT / target.lstrip("/")
        else:
            resolved = skill_dir / target
        if not resolved.exists():
            errors.append("broken relative link: %s" % match.group(1))
    return errors


def validate_evals_json(path: Path) -> list[str]:
    """Validate the shape of an evals.json file."""
    errors: list[str] = []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return ["evals.json is not valid JSON: %s" % exc]
    if not isinstance(data, dict):
        return ["evals.json must be a JSON object"]
    if "evals" not in data or not isinstance(data["evals"], list):
        errors.append("evals.json missing 'evals' list")
        return errors
    seen_ids = set()
    for idx, ev in enumerate(data["evals"]):
        label = "evals[%d]" % idx
        if not isinstance(ev, dict):
            errors.append("%s must be an object" % label)
            continue
        if "id" not in ev:
            errors.append("%s missing 'id'" % label)
        elif ev["id"] in seen_ids:
            errors.append("%s duplicate id: %r" % (label, ev["id"]))
        else:
            seen_ids.add(ev["id"])
        if not ev.get("prompt"):
            errors.append("%s missing 'prompt'" % label)
        expectations = ev.get("expectations")
        if not isinstance(expectations, list) or not expectations:
            errors.append("%s must have a non-empty 'expectations' list" % label)
    return errors


def validate_trigger_eval_json(path: Path) -> list[str]:
    """Validate the shape of a trigger_eval.json file."""
    errors: list[str] = []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return ["trigger_eval.json is not valid JSON: %s" % exc]
    if not isinstance(data, list) or not data:
        return ["trigger_eval.json must be a non-empty JSON array"]
    for idx, item in enumerate(data):
        label = "trigger_eval[%d]" % idx
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        if not item.get("query"):
            errors.append("%s missing 'query'" % label)
        if not isinstance(item.get("should_trigger"), bool):
            errors.append("%s 'should_trigger' must be a boolean" % label)
    return errors


def validate_skill(skill_dir: Path, evals_dir: Path = EVALS_DIR) -> list[str]:
    """Validate one skill directory. Returns a list of error strings."""
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["missing SKILL.md"]

    content = skill_md.read_text()
    try:
        fields = parse_frontmatter(content)
    except ValueError as exc:
        errors.append(str(exc))
    else:
        errors.extend(validate_frontmatter(fields, skill_dir.name))
        errors.extend(validate_relative_links(content, skill_dir))

    skill_evals_dir = evals_dir / skill_dir.name
    evals_json = skill_evals_dir / "evals.json"
    trigger_json = skill_evals_dir / "trigger_eval.json"
    if evals_json.exists():
        errors.extend(validate_evals_json(evals_json))
    if trigger_json.exists():
        errors.extend(validate_trigger_eval_json(trigger_json))
    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        skill_dirs = []
        for name in args:
            skill_dir = REPO_ROOT / name
            if not skill_dir.is_dir():
                print("Error: no such skill directory: %s" % name, file=sys.stderr)
                return 2
            skill_dirs.append(skill_dir)
    else:
        skill_dirs = discover_skill_dirs()

    total_errors = 0
    for skill_dir in skill_dirs:
        errors = validate_skill(skill_dir)
        if errors:
            total_errors += len(errors)
            print("FAIL %s" % skill_dir.name)
            for err in errors:
                print("  - %s" % err)
        else:
            print("OK   %s" % skill_dir.name)

    if total_errors:
        print("\n%d validation error(s) across %d skill(s)" % (total_errors, len(skill_dirs)), file=sys.stderr)
        return 1
    print("\nAll %d skill(s) valid" % len(skill_dirs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
