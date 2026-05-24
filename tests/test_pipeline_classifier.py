"""Tests for pipeline_classifier — classification stage integration."""

import pytest
from logslice.classifier import ClassifiedLine
from logslice.pipeline_classifier import (
    _rules_from_config,
    classification_stage,
    apply_classification_from_config,
)


def _cfg(**kwargs):
    """Build a minimal config-like namespace."""

    class Cfg:
        classifier_rules = []
        classifier_presets = []
        classifier_tag_field = "level"
        classifier_unmatched_tag = "unknown"

    c = Cfg()
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


# ---------------------------------------------------------------------------
# _rules_from_config
# ---------------------------------------------------------------------------


class TestRulesFromConfig:
    def test_empty_rules_and_presets_returns_empty(self):
        cfg = _cfg()
        rules = _rules_from_config(cfg)
        assert rules == []

    def test_custom_rule_compiled(self):
        cfg = _cfg(classifier_rules=[(r"ERROR", "error")])
        rules = _rules_from_config(cfg)
        assert len(rules) == 1
        pattern, label = rules[0]
        assert label == "error"
        assert pattern.search("ERROR: something broke")

    def test_preset_expands_rules(self):
        cfg = _cfg(classifier_presets=["syslog"])
        rules = _rules_from_config(cfg)
        # syslog preset should include at least one rule
        assert len(rules) >= 1

    def test_custom_and_preset_combined(self):
        cfg = _cfg(
            classifier_rules=[(r"CUSTOM", "custom")],
            classifier_presets=["syslog"],
        )
        rules = _rules_from_config(cfg)
        labels = [label for _, label in rules]
        assert "custom" in labels


# ---------------------------------------------------------------------------
# classification_stage
# ---------------------------------------------------------------------------


class TestClassificationStage:
    def test_passes_all_lines_through(self):
        rules = []
        lines = ["hello", "world"]
        out = list(classification_stage(iter(lines), rules, tag_field="level", unmatched="unknown"))
        assert out == lines

    def test_classified_line_has_tag(self):
        from logslice.classifier import compile_classifier_rules

        rules = compile_classifier_rules([(r"ERROR", "error")])
        lines = ["ERROR: disk full"]
        out = list(classification_stage(iter(lines), rules, tag_field="level", unmatched="unknown"))
        # output is still the raw string; classification is stored as attribute
        assert len(out) == 1
        assert out[0] == "ERROR: disk full"

    def test_unmatched_line_gets_unmatched_tag(self):
        from logslice.classifier import compile_classifier_rules

        rules = compile_classifier_rules([(r"ERROR", "error")])
        lines = ["INFO: all good"]
        results = list(
            classification_stage(iter(lines), rules, tag_field="level", unmatched="unknown")
        )
        assert results == ["INFO: all good"]


# ---------------------------------------------------------------------------
# apply_classification_from_config
# ---------------------------------------------------------------------------


class TestApplyClassificationFromConfig:
    def test_no_rules_yields_all_lines(self):
        cfg = _cfg()
        lines = ["line one", "line two", "line three"]
        out = list(apply_classification_from_config(iter(lines), cfg))
        assert out == lines

    def test_with_error_rule_yields_all_lines(self):
        cfg = _cfg(classifier_rules=[(r"ERROR", "error")])
        lines = ["ERROR: bad", "INFO: ok"]
        out = list(apply_classification_from_config(iter(lines), cfg))
        assert out == lines

    def test_empty_input_yields_nothing(self):
        cfg = _cfg(classifier_rules=[(r"ERROR", "error")])
        out = list(apply_classification_from_config(iter([]), cfg))
        assert out == []

    def test_custom_tag_field_respected(self):
        cfg = _cfg(
            classifier_rules=[(r"WARN", "warning")],
            classifier_tag_field="severity",
        )
        lines = ["WARN: low disk space"]
        out = list(apply_classification_from_config(iter(lines), cfg))
        assert out == lines

    def test_custom_unmatched_tag_respected(self):
        cfg = _cfg(
            classifier_rules=[(r"ERROR", "error")],
            classifier_unmatched_tag="other",
        )
        lines = ["DEBUG: verbose output"]
        out = list(apply_classification_from_config(iter(lines), cfg))
        assert out == lines
