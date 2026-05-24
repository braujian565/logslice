"""Tests for logslice.labeler."""

import pytest

from logslice.labeler import (
    compile_label_rules,
    label_all,
    label_line,
    label_lines,
)


class TestCompileLabelRules:
    def test_returns_compiled_patterns(self):
        rules = compile_label_rules([("error", r"ERROR")])
        assert len(rules) == 1
        label, pat = rules[0]
        assert label == "error"
        assert pat.search("ERROR occurred")

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            compile_label_rules([("" , r"foo")])

    def test_invalid_regex_raises(self):
        with pytest.raises(ValueError, match="Invalid regex"):
            compile_label_rules([("bad", r"[unclosed")])

    def test_multiple_rules(self):
        rules = compile_label_rules([("a", r"AAA"), ("b", r"BBB")])
        assert len(rules) == 2


class TestLabelLine:
    def setup_method(self):
        self.rules = compile_label_rules([("error", r"ERROR"), ("warn", r"WARN")])

    def test_matches_first_rule(self):
        assert label_line("ERROR: disk full", self.rules) == "error"

    def test_matches_second_rule(self):
        assert label_line("WARN: low memory", self.rules) == "warn"

    def test_no_match_returns_none(self):
        assert label_line("INFO: all good", self.rules) is None

    def test_first_match_wins(self):
        rules = compile_label_rules([("first", r"X"), ("second", r"X")])
        assert label_line("X", rules) == "first"


class TestLabelAll:
    def setup_method(self):
        self.rules = compile_label_rules([("error", r"ERROR"), ("critical", r"CRIT")])

    def test_returns_all_matching_labels(self):
        labels = label_all("ERROR CRIT", self.rules)
        assert labels == ["error", "critical"]

    def test_no_match_returns_empty(self):
        assert label_all("INFO message", self.rules) == []


class TestLabelLines:
    def setup_method(self):
        self.rules = compile_label_rules([("error", r"ERROR"), ("warn", r"WARN")])

    def test_yields_line_and_labels(self):
        result = list(label_lines(["ERROR here"], self.rules))
        assert result == [("ERROR here", ["error"])]

    def test_no_match_empty_labels(self):
        result = list(label_lines(["INFO ok"], self.rules))
        assert result == [("INFO ok", [])]

    def test_default_label_applied(self):
        result = list(label_lines(["INFO ok"], self.rules, default="other"))
        assert result == [("INFO ok", ["other"])]

    def test_multi_collects_all(self):
        result = list(label_lines(["ERROR WARN"], self.rules, multi=True))
        assert result == [("ERROR WARN", ["error", "warn"])]

    def test_empty_input_yields_nothing(self):
        assert list(label_lines([], self.rules)) == []
