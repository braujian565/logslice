"""Tests for logslice.redactor."""

import pytest
from logslice.redactor import (
    compile_redaction_rules,
    redact_line,
    redact_lines,
    PRESETS,
)


class TestCompileRedactionRules:
    def test_returns_list_of_tuples(self):
        rules = compile_redaction_rules([r"\d+"])
        assert len(rules) == 1
        pattern, replacement = rules[0]
        assert pattern.pattern == r"\d+"
        assert replacement == "[REDACTED]"

    def test_preset_name_expands(self):
        rules = compile_redaction_rules(["ipv4"])
        pattern, _ = rules[0]
        assert pattern.pattern == PRESETS["ipv4"]

    def test_custom_replacement(self):
        rules = compile_redaction_rules([r"\d+"], replacement="***")
        _, replacement = rules[0]
        assert replacement == "***"

    def test_multiple_patterns(self):
        rules = compile_redaction_rules([r"foo", r"bar"])
        assert len(rules) == 2

    def test_unknown_name_treated_as_regex(self):
        rules = compile_redaction_rules([r"custom_\w+"])
        pattern, _ = rules[0]
        assert pattern.search("custom_value")


class TestRedactLine:
    def test_replaces_match(self):
        rules = compile_redaction_rules([r"secret"])
        assert redact_line("my secret value", rules) == "my [REDACTED] value"

    def test_no_match_unchanged(self):
        rules = compile_redaction_rules([r"secret"])
        assert redact_line("nothing here", rules) == "nothing here"

    def test_multiple_rules_applied(self):
        rules = compile_redaction_rules([r"foo", r"bar"])
        result = redact_line("foo and bar", rules)
        assert result == "[REDACTED] and [REDACTED]"

    def test_ipv4_preset(self):
        rules = compile_redaction_rules(["ipv4"])
        result = redact_line("client 192.168.1.1 connected", rules)
        assert "192.168.1.1" not in result
        assert "[REDACTED]" in result

    def test_email_preset(self):
        rules = compile_redaction_rules(["email"])
        result = redact_line("user user@example.com logged in", rules)
        assert "user@example.com" not in result

    def test_empty_rules_returns_line(self):
        assert redact_line("unchanged", []) == "unchanged"

    def test_empty_line(self):
        rules = compile_redaction_rules([r"\d+"])
        assert redact_line("", rules) == ""


class TestRedactLines:
    def test_yields_redacted_lines(self):
        rules = compile_redaction_rules([r"\d+"])
        lines = ["abc 123", "def 456", "ghi"]
        result = list(redact_lines(lines, rules))
        assert result == ["abc [REDACTED]", "def [REDACTED]", "ghi"]

    def test_empty_iterable(self):
        rules = compile_redaction_rules([r"\d+"])
        assert list(redact_lines([], rules)) == []

    def test_lazy_generator(self):
        rules = compile_redaction_rules([r"x"])
        gen = redact_lines(iter(["x", "y"]), rules)
        assert next(gen) == "[REDACTED]"
        assert next(gen) == "y"
