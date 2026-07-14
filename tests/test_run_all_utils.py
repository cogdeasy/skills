"""Unit tests for utility functions in evals/run_all.py (no cursor-agent or API required)."""
import pytest
from run_all import (
    _rewrite_skill_frontmatter_name,
    check_expectation,
    extract_negative_terms,
    find_forbidden_reference,
    grade_expectations,
    parse_skill_md,
)

SKILL_MD = """---
name: text-to-speech
description: Convert text to speech.
license: MIT
---

# Body
"""


class TestParseSkillMd:
    def test_parses_name_and_description(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(SKILL_MD)
        name, description, content = parse_skill_md(tmp_path)
        assert name == "text-to-speech"
        assert description == "Convert text to speech."
        assert content == SKILL_MD

    def test_missing_frontmatter_raises(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("# no frontmatter\n")
        with pytest.raises(ValueError, match="missing frontmatter"):
            parse_skill_md(tmp_path)

    def test_missing_name_raises(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("---\ndescription: d\n---\n")
        with pytest.raises(ValueError, match="missing 'name'"):
            parse_skill_md(tmp_path)

    def test_multiline_description(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("---\nname: x\ndescription: >\n  a\n  b\n---\n")
        _, description, _ = parse_skill_md(tmp_path)
        assert description == "a b"


class TestRewriteFrontmatterName:
    def test_rewrites_name(self):
        result = _rewrite_skill_frontmatter_name(SKILL_MD, "text-to-speech-eval-abc123")
        assert "name: text-to-speech-eval-abc123" in result
        assert "description: Convert text to speech." in result

    def test_no_frontmatter_unchanged(self):
        content = "# plain markdown\n"
        assert _rewrite_skill_frontmatter_name(content, "new") == content

    def test_unclosed_frontmatter_unchanged(self):
        content = "---\nname: x\n"
        assert _rewrite_skill_frontmatter_name(content, "new") == content


class TestExtractNegativeTerms:
    def test_extracts_quoted_term(self):
        assert extract_negative_terms("Imports from '@elevenlabs/elevenlabs-js' (NOT 'elevenlabs')") == ["elevenlabs"]

    def test_no_negative(self):
        assert extract_negative_terms("Uses model_id parameter") == []


class TestFindForbiddenReference:
    def test_detects_npm_install(self):
        assert find_forbidden_reference("npm install elevenlabs", "elevenlabs") is not None

    def test_detects_import(self):
        assert find_forbidden_reference('import { X } from "elevenlabs";', "elevenlabs") is not None

    def test_detects_require(self):
        assert find_forbidden_reference('const x = require("elevenlabs")', "elevenlabs") is not None

    def test_scoped_package_not_flagged(self):
        assert find_forbidden_reference('import { X } from "@elevenlabs/elevenlabs-js";', "elevenlabs") is None


class TestCheckExpectation:
    def test_pattern_match_passes(self):
        response = "client.text_to_speech.convert(text=..., model_id=..., voice_id=...)"
        passed, _ = check_expectation(response.lower(), response, "Calls client.text_to_speech.convert()")
        assert passed

    def test_pattern_missing_fails(self):
        response = "print('hello')"
        passed, _ = check_expectation(response.lower(), response, "Calls client.text_to_speech.convert()")
        assert not passed

    def test_deprecated_pattern_fails(self):
        response = "from elevenlabs import generate"
        passed, _ = check_expectation(
            response.lower(), response,
            "Does NOT use the deprecated 'elevenlabs' v1 API",
        )
        assert not passed

    def test_no_deprecated_pattern_passes(self):
        response = "from elevenlabs import ElevenLabs"
        passed, _ = check_expectation(
            response.lower(), response,
            "Does NOT use the deprecated v1 API (no 'from elevenlabs import generate')",
        )
        assert passed


class TestGradeExpectations:
    def test_grades_multiple(self):
        response = "client.text_to_speech.convert(model_id='eleven_multilingual_v2', voice_id='x')"
        grades = grade_expectations(response, ["Specifies a model_id parameter", "Specifies a voice_id parameter"])
        assert len(grades) == 2
        assert all(g["passed"] for g in grades)
