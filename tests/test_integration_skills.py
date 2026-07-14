"""Integration tests: validate every skill directory in the repo end-to-end.

These exercise the real repo contents (no ElevenLabs API access required) plus the
eval harness's dry-run mode as a CLI smoke test.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from run_all import ALL_SKILLS, parse_skill_md
from validate_skills import discover_skill_dirs, validate_skill

REPO_ROOT = Path(__file__).parent.parent
EVALS_DIR = REPO_ROOT / "evals"

SKILL_DIRS = discover_skill_dirs(REPO_ROOT)
SKILL_NAMES = [p.name for p in SKILL_DIRS]


@pytest.mark.integration
class TestEverySkillDirectory:
    def test_skills_discovered(self):
        assert len(SKILL_DIRS) >= 9

    @pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_NAMES)
    def test_skill_validates(self, skill_dir):
        assert validate_skill(skill_dir) == []

    @pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_NAMES)
    def test_skill_parses_with_harness(self, skill_dir):
        name, description, content = parse_skill_md(skill_dir)
        assert name == skill_dir.name
        assert description

    @pytest.mark.parametrize("skill_name", ALL_SKILLS)
    def test_harness_skill_list_matches_repo(self, skill_name):
        assert (REPO_ROOT / skill_name / "SKILL.md").exists()
        assert (EVALS_DIR / skill_name / "evals.json").exists()
        assert (EVALS_DIR / skill_name / "trigger_eval.json").exists()

    def test_repo_skills_covered_by_harness(self):
        top_level = {p.name for p in SKILL_DIRS}
        assert top_level == set(ALL_SKILLS)


@pytest.mark.integration
class TestCliSmoke:
    def test_validate_skills_cli(self):
        result = subprocess.run(
            [sys.executable, str(EVALS_DIR / "validate_skills.py")],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "All" in result.stdout

    def test_run_all_dry_run_cli(self):
        result = subprocess.run(
            [sys.executable, str(EVALS_DIR / "run_all.py"), "--dry-run"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Dry run passed" in result.stderr

    def test_run_all_dry_run_fails_on_missing_skill(self):
        result = subprocess.run(
            [sys.executable, str(EVALS_DIR / "run_all.py"), "--dry-run", "--skills", "no-such-skill"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 1
        assert "skill directory not found" in result.stderr


@pytest.mark.integration
class TestUpstreamSyncPrCli:
    """CLI tests for scripts/upstream_sync_pr.py as invoked by the sync workflow."""

    SCRIPT = REPO_ROOT / "scripts" / "upstream_sync_pr.py"

    ENV = {
        "UPSTREAM_REPO": "elevenlabs/skills",
        "UPSTREAM_BRANCH": "main",
        "BEHIND": "4",
        "AHEAD": "1",
        "COMMIT_LOG": "abc1234 Update skills\ndef5678 Fix docs",
        "CONFLICT_FILES": "",
        "REMOVED_SKILLS": "",
    }

    def run_script(self, *args, **env_overrides):
        env = {**self.ENV, **env_overrides, "PATH": os.environ.get("PATH", "")}
        return subprocess.run(
            [sys.executable, str(self.SCRIPT), *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT), env=env,
        )

    def test_title(self):
        result = self.run_script("--title")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "Sync with upstream: merge 4 commits from elevenlabs/skills"

    def test_body_clean_merge(self):
        result = self.run_script()
        assert result.returncode == 0, result.stderr
        assert "**4 commit(s) behind**" in result.stdout
        assert "abc1234 Update skills" in result.stdout
        assert "The merge completed cleanly with no conflicts." in result.stdout

    def test_body_with_conflicts_and_removed_skills(self):
        result = self.run_script(
            CONFLICT_FILES="agents/SKILL.md\nmusic/SKILL.md",
            REMOVED_SKILLS="setup-api-key",
        )
        assert result.returncode == 0, result.stderr
        assert "[!WARNING]" in result.stdout
        assert "- `agents/SKILL.md`" in result.stdout
        assert "- `music/SKILL.md`" in result.stdout
        assert "- `setup-api-key`" in result.stdout

    def test_invalid_behind_is_an_error(self):
        result = self.run_script(BEHIND="not-a-number")
        assert result.returncode == 1
        assert "must be integers" in result.stderr
