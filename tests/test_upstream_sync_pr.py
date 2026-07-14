"""Unit tests for scripts/upstream_sync_pr.py."""
from datetime import datetime, timezone

from upstream_sync_pr import (
    build_pr_body,
    build_pr_title,
    parse_conflicted_files,
    parse_removed_skills,
)

CHECKED_AT = datetime(2026, 7, 14, 6, 0, tzinfo=timezone.utc)


def make_body(**overrides):
    kwargs = dict(
        upstream_repo="elevenlabs/skills",
        upstream_branch="main",
        behind=3,
        ahead=2,
        commit_log="abc1234 First\ndef5678 Second",
        conflict_files=[],
        removed_skills=[],
        checked_at=CHECKED_AT,
    )
    kwargs.update(overrides)
    return build_pr_body(**kwargs)


class TestParseConflictedFiles:
    def test_empty(self):
        assert parse_conflicted_files("") == []

    def test_splits_and_strips_lines(self):
        assert parse_conflicted_files("a.md\n  b/c.md \n\n") == ["a.md", "b/c.md"]


class TestParseRemovedSkills:
    def test_empty(self):
        assert parse_removed_skills("") == []

    def test_space_separated(self):
        assert parse_removed_skills("setup-api-key music") == ["setup-api-key", "music"]


class TestBuildPrTitle:
    def test_plural(self):
        assert build_pr_title(3, "elevenlabs/skills") == (
            "Sync with upstream: merge 3 commits from elevenlabs/skills"
        )

    def test_singular(self):
        assert "1 commit from" in build_pr_title(1, "elevenlabs/skills")


class TestBuildPrBody:
    def test_includes_counts_and_commit_log(self):
        body = make_body()
        assert "**3 commit(s) behind**" in body
        assert "2 commit(s) ahead" in body
        assert "abc1234 First" in body
        assert "elevenlabs/skills@main" in body

    def test_clean_merge_has_no_conflict_section(self):
        body = make_body()
        assert "The merge completed cleanly with no conflicts." in body
        assert "Conflicted files" not in body
        assert "[!WARNING]" not in body

    def test_conflicts_are_flagged(self):
        body = make_body(conflict_files=["agents/SKILL.md", "README.md"])
        assert "[!WARNING]" in body
        assert "### Conflicted files" in body
        assert "- `agents/SKILL.md`" in body
        assert "- `README.md`" in body
        assert "resolved manually" in body
        assert "The merge completed cleanly" not in body

    def test_removed_skills_section(self):
        body = make_body(removed_skills=["setup-api-key"])
        assert "Skills removed upstream but still present in this fork" in body
        assert "- `setup-api-key`" in body

    def test_no_removed_skills_section_when_empty(self):
        assert "removed upstream" not in make_body()

    def test_empty_commit_log_placeholder(self):
        assert "(no commit log available)" in make_body(commit_log="")

    def test_timestamp_footer(self):
        assert "Generated 2026-07-14 06:00 UTC" in make_body()
