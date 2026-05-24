"""Tests for logslice.classifier and logslice.pipeline_classifier."""

from __future__ import annotations

import pytest

from logslice.classifier import (
    ClassifiedLine,
    classify_line,
    classify_lines,
    compile_classifier_rules,
    preset_rules,
)
from logslice.pipeline_classifier import (
    apply_classification_from_config,
    classification_stage,
)


# ---------------------------------------------------------------------------
# compile_classifier_rules
# ---------------------------------------------------------------------------

class TestCompileClassifierRules:
    def test_returns_compiled_patterns(self):
        rules = compile_classifier_rules([(r"\bERROR\b", "error")])
        assert len(rules) == 1
        pattern, level = rules[0]
        assert hasattr(pattern, "search")
        assert level == "error"

    def test_empty_level_raises(self):
        with pytest.raises(ValueError):
            compile_classifier_rules([(r"ERROR", "")])

    def test_multiple_rules_ordered(self):
        rules = compile_classifier_rules([
            (r"CRITICAL", "critical"),
            (r"ERROR", "error"),
        ])
        assert [lvl for _, lvl in rules] == ["critical", "error"]


# ---------------------------------------------------------------------------
# classify_line
# ---------------------------------------------------------------------------

class TestClassifyLine:
    def setup_method(self):
        self.rules = preset_rules()

    def test_detects_error(self):
        assert classify_line("2024-01-01 ERROR something failed", self.rules) == "error"

    def test_detects_warning(self):
        assert classify_line("WARN disk almost full", self.rules) == "warning"

    def test_detects_critical(self):
        assert classify_line("CRITICAL system down", self.rules) == "critical"

    def test_detects_info(self):
        assert classify_line("INFO server started", self.rules) == "info"

    def test_detects_debug(self):
        assert classify_line("DEBUG entering loop", self.rules) == "debug"

    def test_no_match_returns_default(self):
        assert classify_line("plain log line", self.rules, default_level="unknown") == "unknown"

    def test_no_match_returns_none_by_default(self):
        assert classify_line("plain log line", self.rules) is None

    def test_first_rule_wins(self):
        # CRITICAL appears before ERROR in default preset
        assert classify_line("CRITICAL ERROR both", self.rules) == "critical"


# ---------------------------------------------------------------------------
# classify_lines
# ---------------------------------------------------------------------------

class TestClassifyLines:
    def test_yields_classified_lines(self):
        rules = preset_rules()
        lines = ["INFO start", "ERROR boom", "plain"]
        results = list(classify_lines(lines, rules))
        assert len(results) == 3
        assert results[0].level == "info"
        assert results[1].level == "error"
        assert results[2].level is None

    def test_lineno_starts_at_one(self):
        rules = preset_rules()
        results = list(classify_lines(["INFO a", "ERROR b"], rules))
        assert results[0].lineno == 1
        assert results[1].lineno == 2

    def test_custom_start(self):
        rules = preset_rules()
        results = list(classify_lines(["INFO a"], rules, start=10))
        assert results[0].lineno == 10

    def test_empty_input_yields_nothing(self):
        assert list(classify_lines([], preset_rules())) == []


# ---------------------------------------------------------------------------
# preset_rules
# ---------------------------------------------------------------------------

def test_preset_rules_default_returns_rules():
    rules = preset_rules("default")
    assert len(rules) > 0


def test_preset_rules_unknown_raises():
    with pytest.raises(KeyError):
        preset_rules("nonexistent")


# ---------------------------------------------------------------------------
# pipeline_classifier — apply_classification_from_config
# ---------------------------------------------------------------------------

def _cfg(**kwargs):
    from logslice.config import LogSliceConfig
    cfg = LogSliceConfig()
    for k, v in kwargs.items():
        setattr(cfg, k, v)
    return cfg


class TestApplyClassificationFromConfig:
    def test_disabled_yields_all_lines_unchanged(self):
        cfg = _cfg(classify=False)
        lines = ["INFO start", "ERROR boom"]
        result = list(apply_classification_from_config(lines, cfg))
        assert result == lines

    def test_enabled_yields_all_lines_unchanged(self):
        cfg = _cfg(classify=True)
        lines = ["INFO start", "ERROR boom"]
        result = list(apply_classification_from_config(lines, cfg))
        assert result == lines

    def test_callback_receives_classified_lines(self):
        cfg = _cfg(classify=True)
        collected: list = []
        list(apply_classification_from_config(
            ["INFO a", "ERROR b"],
            cfg,
            callback=collected.append,
        ))
        assert len(collected) == 2
        assert collected[0].level == "info"
        assert collected[1].level == "error"

    def test_no_callback_does_not_raise(self):
        cfg = _cfg(classify=True)
        result = list(apply_classification_from_config(["INFO ok"], cfg))
        assert result == ["INFO ok"]

    def test_extra_rules_applied(self):
        cfg = _cfg(classify=True, classifier_rules=[(r"TRACE", "trace")])
        collected: list = []
        list(apply_classification_from_config(
            ["TRACE verbose"],
            cfg,
            callback=collected.append,
        ))
        assert any(cl.level in ("trace", "debug", "info") for cl in collected)
