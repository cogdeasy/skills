#!/usr/bin/env python3
"""Build the title and body for the automated upstream-sync pull request.

Used by .github/workflows/upstream-sync-check.yml. All inputs come from
environment variables so the workflow can pass along what it measured:

    UPSTREAM_REPO    e.g. "elevenlabs/skills"
    UPSTREAM_BRANCH  e.g. "main"
    BEHIND           number of commits the fork is behind upstream
    AHEAD            number of commits the fork is ahead of upstream
    COMMIT_LOG       oneline log of the missing upstream commits
    CONFLICT_FILES   newline-separated paths that conflicted during the merge
    REMOVED_SKILLS   space-separated skill dirs deleted upstream but kept here

Prints the PR body to stdout by default, or the PR title with --title.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

CONFLICT_WARNING = (
    "> [!WARNING]\n"
    "> This merge had conflicts. The conflicted files were committed with their\n"
    "> conflict markers left in place and **must be resolved manually** before\n"
    "> this PR is merged."
)


def parse_conflicted_files(text: str) -> list[str]:
    """Parse newline-separated conflict paths (e.g. from `git diff --diff-filter=U`)."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_removed_skills(text: str) -> list[str]:
    """Parse the space-separated removed-skills list produced by the workflow."""
    return [part for part in text.split() if part]


def build_pr_title(behind: int, upstream_repo: str) -> str:
    plural = "" if behind == 1 else "s"
    return f"Sync with upstream: merge {behind} commit{plural} from {upstream_repo}"


def build_pr_body(
    upstream_repo: str,
    upstream_branch: str,
    behind: int,
    ahead: int,
    commit_log: str,
    conflict_files: list[str],
    removed_skills: list[str],
    checked_at: datetime | None = None,
) -> str:
    checked_at = checked_at or datetime.now(timezone.utc)
    lines = [
        "## Upstream sync",
        "",
        f"Merges `upstream/{upstream_branch}` from [{upstream_repo}]"
        f"(https://github.com/{upstream_repo}) into this fork.",
        "",
        f"The fork was **{behind} commit(s) behind** and {ahead} commit(s) ahead "
        f"of `{upstream_repo}@{upstream_branch}` when this PR was generated.",
        "",
        "### Upstream commits included",
        "```",
        commit_log.strip() or "(no commit log available)",
        "```",
    ]
    if conflict_files:
        lines += ["", CONFLICT_WARNING, "", "### Conflicted files"]
        lines += [f"- `{path}`" for path in conflict_files]
    else:
        lines += ["", "The merge completed cleanly with no conflicts."]
    if removed_skills:
        lines += [
            "",
            "### Skills removed upstream but still present in this fork",
            *[f"- `{skill}`" for skill in removed_skills],
            "",
            "Consider removing these skill directories (and their `evals/` configs) "
            "to match upstream.",
        ]
    lines += [
        "",
        "---",
        f"_Generated {checked_at.strftime('%Y-%m-%d %H:%M UTC')} by the scheduled "
        "upstream-sync workflow. This PR is force-updated on each run until merged._",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", action="store_true", help="print the PR title instead of the body")
    args = parser.parse_args(argv)

    upstream_repo = os.environ.get("UPSTREAM_REPO", "elevenlabs/skills")
    upstream_branch = os.environ.get("UPSTREAM_BRANCH", "main")
    try:
        behind = int(os.environ.get("BEHIND", "0"))
        ahead = int(os.environ.get("AHEAD", "0"))
    except ValueError:
        print("BEHIND and AHEAD must be integers", file=sys.stderr)
        return 1

    if args.title:
        print(build_pr_title(behind, upstream_repo))
        return 0

    body = build_pr_body(
        upstream_repo=upstream_repo,
        upstream_branch=upstream_branch,
        behind=behind,
        ahead=ahead,
        commit_log=os.environ.get("COMMIT_LOG", ""),
        conflict_files=parse_conflicted_files(os.environ.get("CONFLICT_FILES", "")),
        removed_skills=parse_removed_skills(os.environ.get("REMOVED_SKILLS", "")),
    )
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
