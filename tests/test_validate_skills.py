"""Unit tests for evals/validate_skills.py."""
import json

import pytest
from validate_skills import (
    parse_frontmatter,
    validate_evals_json,
    validate_frontmatter,
    validate_relative_links,
    validate_skill,
    validate_trigger_eval_json,
)

VALID_SKILL_MD = """---
name: my-skill
description: Does a thing. Use when the user asks for the thing.
license: MIT
compatibility: Requires internet access.
metadata: {"openclaw": {"requires": {"env": ["ELEVENLABS_API_KEY"]}}}
---

# My Skill

Body text.
"""


class TestParseFrontmatter:
    def test_parses_all_fields(self):
        fields = parse_frontmatter(VALID_SKILL_MD)
        assert fields["name"] == "my-skill"
        assert fields["description"].startswith("Does a thing")
        assert fields["license"] == "MIT"
        assert "openclaw" in fields["metadata"]

    def test_missing_opening_delimiter(self):
        with pytest.raises(ValueError, match="missing frontmatter"):
            parse_frontmatter("# No frontmatter\n")

    def test_missing_closing_delimiter(self):
        with pytest.raises(ValueError, match="closing"):
            parse_frontmatter("---\nname: x\n# never closed\n")

    def test_multiline_description(self):
        content = "---\nname: x\ndescription: >\n  line one\n  line two\n---\n"
        fields = parse_frontmatter(content)
        assert fields["description"] == "line one line two"

    def test_malformed_line_raises(self):
        with pytest.raises(ValueError, match="malformed"):
            parse_frontmatter("---\nnot a key value\n---\n")

    def test_strips_quotes(self):
        fields = parse_frontmatter('---\nname: "quoted"\ndescription: \'single\'\n---\n')
        assert fields["name"] == "quoted"
        assert fields["description"] == "single"

    def test_skips_blank_and_comment_lines(self):
        fields = parse_frontmatter("---\n\n# comment\nname: x\ndescription: y\n---\n")
        assert fields["name"] == "x"


class TestValidateFrontmatter:
    def test_valid(self):
        fields = parse_frontmatter(VALID_SKILL_MD)
        assert validate_frontmatter(fields, "my-skill") == []

    def test_missing_name(self):
        errors = validate_frontmatter({"description": "d"}, "my-skill")
        assert any("missing required field: name" in e for e in errors)

    def test_missing_description(self):
        errors = validate_frontmatter({"name": "my-skill"}, "my-skill")
        assert any("missing required field: description" in e for e in errors)

    def test_name_directory_mismatch(self):
        errors = validate_frontmatter({"name": "other", "description": "d"}, "my-skill")
        assert any("does not match directory" in e for e in errors)

    def test_invalid_name_format(self):
        errors = validate_frontmatter({"name": "Bad_Name", "description": "d"}, "Bad_Name")
        assert any("lowercase" in e for e in errors)

    def test_name_too_long(self):
        long_name = "a" * 65
        errors = validate_frontmatter({"name": long_name, "description": "d"}, long_name)
        assert any("exceeds 64" in e for e in errors)

    def test_description_too_long(self):
        errors = validate_frontmatter({"name": "my-skill", "description": "x" * 1025}, "my-skill")
        assert any("description exceeds" in e for e in errors)

    def test_invalid_metadata_json(self):
        errors = validate_frontmatter(
            {"name": "my-skill", "description": "d", "metadata": "{not json"}, "my-skill"
        )
        assert any("metadata is not valid JSON" in e for e in errors)

    def test_unknown_field(self):
        errors = validate_frontmatter(
            {"name": "my-skill", "description": "d", "bogus": "x"}, "my-skill"
        )
        assert any("unknown frontmatter field: bogus" in e for e in errors)


class TestValidateRelativeLinks:
    def test_existing_link_ok(self, tmp_path):
        (tmp_path / "references").mkdir()
        (tmp_path / "references" / "guide.md").write_text("hi")
        errors = validate_relative_links("See [guide](references/guide.md).", tmp_path)
        assert errors == []

    def test_broken_link_reported(self, tmp_path):
        errors = validate_relative_links("See [guide](references/missing.md).", tmp_path)
        assert any("broken relative link" in e for e in errors)

    def test_external_links_ignored(self, tmp_path):
        content = "[a](https://example.com) [b](mailto:x@y.z) [c](#anchor)"
        assert validate_relative_links(content, tmp_path) == []

    def test_anchor_within_relative_link(self, tmp_path):
        (tmp_path / "doc.md").write_text("hi")
        assert validate_relative_links("[a](doc.md#section)", tmp_path) == []


class TestValidateEvalsJson:
    def _write(self, tmp_path, data):
        p = tmp_path / "evals.json"
        p.write_text(json.dumps(data) if not isinstance(data, str) else data)
        return p

    def test_valid(self, tmp_path):
        p = self._write(tmp_path, {"evals": [{"id": 1, "prompt": "p", "expectations": ["e"]}]})
        assert validate_evals_json(p) == []

    def test_invalid_json(self, tmp_path):
        p = self._write(tmp_path, "{broken")
        assert any("not valid JSON" in e for e in validate_evals_json(p))

    def test_missing_evals_key(self, tmp_path):
        p = self._write(tmp_path, {"skill_name": "x"})
        assert any("missing 'evals'" in e for e in validate_evals_json(p))

    def test_missing_prompt(self, tmp_path):
        p = self._write(tmp_path, {"evals": [{"id": 1, "expectations": ["e"]}]})
        assert any("missing 'prompt'" in e for e in validate_evals_json(p))

    def test_duplicate_ids(self, tmp_path):
        p = self._write(tmp_path, {"evals": [
            {"id": 1, "prompt": "a", "expectations": ["e"]},
            {"id": 1, "prompt": "b", "expectations": ["e"]},
        ]})
        assert any("duplicate id" in e for e in validate_evals_json(p))

    def test_empty_expectations(self, tmp_path):
        p = self._write(tmp_path, {"evals": [{"id": 1, "prompt": "a", "expectations": []}]})
        assert any("expectations" in e for e in validate_evals_json(p))


class TestValidateTriggerEvalJson:
    def _write(self, tmp_path, data):
        p = tmp_path / "trigger_eval.json"
        p.write_text(json.dumps(data) if not isinstance(data, str) else data)
        return p

    def test_valid(self, tmp_path):
        p = self._write(tmp_path, [{"query": "q", "should_trigger": True}])
        assert validate_trigger_eval_json(p) == []

    def test_invalid_json(self, tmp_path):
        p = self._write(tmp_path, "[broken")
        assert any("not valid JSON" in e for e in validate_trigger_eval_json(p))

    def test_not_a_list(self, tmp_path):
        p = self._write(tmp_path, {"query": "q"})
        assert any("non-empty JSON array" in e for e in validate_trigger_eval_json(p))

    def test_missing_query(self, tmp_path):
        p = self._write(tmp_path, [{"should_trigger": True}])
        assert any("missing 'query'" in e for e in validate_trigger_eval_json(p))

    def test_should_trigger_not_bool(self, tmp_path):
        p = self._write(tmp_path, [{"query": "q", "should_trigger": "yes"}])
        assert any("must be a boolean" in e for e in validate_trigger_eval_json(p))


class TestValidateSkill:
    def test_valid_skill_dir(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD)
        assert validate_skill(skill_dir, evals_dir=tmp_path / "evals") == []

    def test_missing_skill_md(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        assert validate_skill(skill_dir, evals_dir=tmp_path / "evals") == ["missing SKILL.md"]

    def test_reports_eval_config_errors(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD)
        evals_dir = tmp_path / "evals" / "my-skill"
        evals_dir.mkdir(parents=True)
        (evals_dir / "evals.json").write_text("{broken")
        errors = validate_skill(skill_dir, evals_dir=tmp_path / "evals")
        assert any("not valid JSON" in e for e in errors)
