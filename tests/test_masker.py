"""Tests for logslice.masker and logslice.pipeline_masker."""

import pytest

from logslice.masker import (
    _build_mask,
    compile_mask_rules,
    mask_line,
    mask_lines,
    PRESETS,
)
from logslice.pipeline_masker import apply_masking_from_config


# ---------------------------------------------------------------------------
# _build_mask
# ---------------------------------------------------------------------------

class TestBuildMask:
    def test_visible_zero_replaces_all(self):
        assert _build_mask("secret", 0, "*") == "******"

    def test_visible_four_keeps_last_four(self):
        result = _build_mask("1234567890", 4, "*")
        assert result == "******7890"

    def test_visible_exceeds_length_replaces_all(self):
        result = _build_mask("abc", 10, "#")
        assert result == "###"

    def test_custom_char_used(self):
        result = _build_mask("hello", 2, "-")
        assert result == "---lo"


# ---------------------------------------------------------------------------
# compile_mask_rules
# ---------------------------------------------------------------------------

class TestCompileMaskRules:
    def test_returns_list_of_tuples(self):
        rules = compile_mask_rules(["email"])
        assert isinstance(rules, list)
        assert len(rules) == 1
        pattern, visible, char = rules[0]
        assert hasattr(pattern, "sub")
        assert visible == 4
        assert char == "*"

    def test_preset_name_resolved(self):
        rules = compile_mask_rules(["ipv4"])
        pattern, _, _ = rules[0]
        assert pattern.search("connect from 192.168.1.1 ok")

    def test_custom_regex_accepted(self):
        rules = compile_mask_rules([r"\bTOKEN-\w+\b"])
        pattern, _, _ = rules[0]
        assert pattern.search("auth TOKEN-abc123")

    def test_custom_visible_and_char(self):
        rules = compile_mask_rules(["ssn"], visible=2, char="#")
        _, visible, char = rules[0]
        assert visible == 2
        assert char == "#"


# ---------------------------------------------------------------------------
# mask_line
# ---------------------------------------------------------------------------

class TestMaskLine:
    def test_email_masked(self):
        rules = compile_mask_rules(["email"], visible=4)
        result = mask_line("user: alice@example.com logged in", rules)
        assert "alice@example.com" not in result
        assert ".com" in result  # last 4 chars visible

    def test_ipv4_masked(self):
        rules = compile_mask_rules(["ipv4"], visible=0)
        result = mask_line("request from 10.0.0.1", rules)
        assert "10.0.0.1" not in result
        assert "*" in result

    def test_no_match_returns_original(self):
        rules = compile_mask_rules(["credit_card"])
        line = "nothing sensitive here"
        assert mask_line(line, rules) == line

    def test_multiple_rules_applied(self):
        rules = compile_mask_rules(["email", "ipv4"], visible=2)
        line = "user bob@test.org from 1.2.3.4"
        result = mask_line(line, rules)
        assert "bob@test.org" not in result
        assert "1.2.3.4" not in result


# ---------------------------------------------------------------------------
# mask_lines generator
# ---------------------------------------------------------------------------

def test_mask_lines_yields_all():
    rules = compile_mask_rules(["email"], visible=4)
    lines = ["a@b.com", "no email here", "x@y.org"]
    out = list(mask_lines(lines, rules))
    assert len(out) == 3
    assert "a@b.com" not in out[0]
    assert out[1] == "no email here"


# ---------------------------------------------------------------------------
# apply_masking_from_config
# ---------------------------------------------------------------------------

class _Cfg:
    mask_patterns = []
    mask_visible_chars = 4
    mask_char = "*"


def test_no_patterns_yields_unchanged():
    cfg = _Cfg()
    lines = ["hello world", "foo bar"]
    assert list(apply_masking_from_config(lines, cfg)) == lines


def test_config_patterns_applied():
    cfg = _Cfg()
    cfg.mask_patterns = ["email"]
    cfg.mask_visible_chars = 4
    cfg.mask_char = "*"
    lines = ["contact admin@example.com now"]
    result = list(apply_masking_from_config(lines, cfg))
    assert "admin@example.com" not in result[0]


def test_missing_attr_defaults_gracefully():
    class MinimalCfg:
        pass
    lines = ["test line"]
    result = list(apply_masking_from_config(lines, MinimalCfg()))
    assert result == lines
