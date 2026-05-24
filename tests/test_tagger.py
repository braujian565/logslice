"""Tests for logslice.tagger and logslice.pipeline_tagger."""

from __future__ import annotations

import pytest

from logslice.tagger import (
    TaggedLine,
    compile_tag_rules,
    tag_line,
    tag_lines,
)
from logslice.pipeline_tagger import apply_tagging_from_config


# ---------------------------------------------------------------------------
# TaggedLine
# ---------------------------------------------------------------------------

class TestTaggedLine:
    def test_str_no_tags_returns_line(self):
        tl = TaggedLine(line="hello world")
        assert str(tl) == "hello world"

    def test_str_with_tags_appends_them(self):
        tl = TaggedLine(line="hello", tags={"env": "prod"})
        assert str(tl) == "hello [env=prod]"

    def test_str_multiple_tags_sorted(self):
        tl = TaggedLine(line="msg", tags={"z": "1", "a": "2"})
        result = str(tl)
        assert "a=2" in result
        assert "z=1" in result
        assert result.index("a=") < result.index("z=")

    def test_str_strips_trailing_newline(self):
        tl = TaggedLine(line="line\n", tags={"k": "v"})
        assert str(tl).startswith("line ")


# ---------------------------------------------------------------------------
# compile_tag_rules
# ---------------------------------------------------------------------------

class TestCompileTagRules:
    def test_returns_list_of_tuples(self):
        rules = compile_tag_rules([{"pattern": r"ERROR", "key": "level", "value": "error"}])
        assert len(rules) == 1
        pattern, key, value = rules[0]
        assert key == "level"
        assert value == "error"

    def test_empty_key_raises(self):
        with pytest.raises(ValueError, match="key"):
            compile_tag_rules([{"pattern": r"x", "key": "", "value": "v"}])

    def test_empty_pattern_raises(self):
        with pytest.raises(ValueError, match="pattern"):
            compile_tag_rules([{"pattern": "", "key": "k", "value": "v"}])

    def test_multiple_rules(self):
        rules = compile_tag_rules([
            {"pattern": r"ERROR", "key": "level", "value": "error"},
            {"pattern": r"WARN", "key": "level", "value": "warn"},
        ])
        assert len(rules) == 2


# ---------------------------------------------------------------------------
# tag_line
# ---------------------------------------------------------------------------

class TestTagLine:
    def test_matching_rule_sets_tag(self):
        rules = compile_tag_rules([{"pattern": r"ERROR", "key": "level", "value": "error"}])
        tl = tag_line("2024-01-01 ERROR something broke", rules)
        assert tl.tags == {"level": "error"}

    def test_no_match_yields_empty_tags(self):
        rules = compile_tag_rules([{"pattern": r"ERROR", "key": "level", "value": "error"}])
        tl = tag_line("INFO all good", rules)
        assert tl.tags == {}

    def test_capture_group_used_when_value_empty(self):
        rules = compile_tag_rules([{"pattern": r"user=(\w+)", "key": "user", "value": ""}])
        tl = tag_line("login user=alice ok", rules)
        assert tl.tags == {"user": "alice"}

    def test_full_match_used_when_no_group_and_no_value(self):
        rules = compile_tag_rules([{"pattern": r"WARN", "key": "flag", "value": ""}])
        tl = tag_line("WARN disk low", rules)
        assert tl.tags == {"flag": "WARN"}


# ---------------------------------------------------------------------------
# tag_lines
# ---------------------------------------------------------------------------

def test_tag_lines_yields_tagged_line_per_input():
    rules = compile_tag_rules([{"pattern": r"ERROR", "key": "level", "value": "error"}])
    results = list(tag_lines(["ERROR foo", "INFO bar"], rules))
    assert len(results) == 2
    assert results[0].tags == {"level": "error"}
    assert results[1].tags == {}


# ---------------------------------------------------------------------------
# apply_tagging_from_config
# ---------------------------------------------------------------------------

def _cfg(**kwargs):
    class Cfg:
        pass
    c = Cfg()
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


def test_no_rules_passes_lines_through():
    cfg = _cfg(tag_rules=[])
    lines = ["hello", "world"]
    result = list(apply_tagging_from_config(lines, cfg))
    assert result == lines


def test_with_rules_applies_tags():
    cfg = _cfg(tag_rules=[{"pattern": r"ERROR", "key": "level", "value": "error"}])
    result = list(apply_tagging_from_config(["ERROR boom", "INFO ok"], cfg, stringify=True))
    assert "level=error" in result[0]
    assert "[" not in result[1]
