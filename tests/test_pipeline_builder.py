"""Tests for logslice.pipeline_builder, including redaction stage."""

import sys
import pytest
from logslice.config import LogSliceConfig
from logslice.pipeline_builder import stages_from_config
from logslice.pipeline import run_pipeline


def _cfg(**kwargs) -> LogSliceConfig:
    return LogSliceConfig(input=sys.stdin, **kwargs)


class TestStagesFromConfig:
    def test_no_filters_returns_all(self):
        cfg = _cfg()
        stages = stages_from_config(cfg)
        lines = ["a", "b", "c"]
        assert list(run_pipeline(iter(lines), stages)) == lines

    def test_include_filter_keeps_matching(self):
        cfg = _cfg(include=[r"error"])
        stages = stages_from_config(cfg)
        lines = ["info ok", "error bad", "warn ok"]
        assert list(run_pipeline(iter(lines), stages)) == ["error bad"]

    def test_exclude_filter_removes_matching(self):
        cfg = _cfg(exclude=[r"debug"])
        stages = stages_from_config(cfg)
        lines = ["info ok", "debug noise", "warn ok"]
        assert list(run_pipeline(iter(lines), stages)) == ["info ok", "warn ok"]

    def test_include_and_exclude_combined(self):
        cfg = _cfg(include=[r"error"], exclude=[r"ignore"])
        stages = stages_from_config(cfg)
        lines = ["error keep", "error ignore this", "info skip"]
        assert list(run_pipeline(iter(lines), stages)) == ["error keep"]

    def test_redact_single_pattern(self):
        cfg = _cfg(redact=[r"\d+"])
        stages = stages_from_config(cfg)
        lines = ["user 42 logged in", "no digits here"]
        result = list(run_pipeline(iter(lines), stages))
        assert result == ["user [REDACTED] logged in", "no digits here"]

    def test_redact_preset_ipv4(self):
        cfg = _cfg(redact=["ipv4"])
        stages = stages_from_config(cfg)
        lines = ["connect from 10.0.0.1", "no ip"]
        result = list(run_pipeline(iter(lines), stages))
        assert "10.0.0.1" not in result[0]
        assert result[1] == "no ip"

    def test_redact_custom_replacement(self):
        cfg = _cfg(redact=[r"secret"], redact_replacement="***")
        stages = stages_from_config(cfg)
        lines = ["my secret key"]
        result = list(run_pipeline(iter(lines), stages))
        assert result == ["my *** key"]

    def test_redact_applied_after_include_filter(self):
        """Redaction should only see lines that passed the include filter."""
        cfg = _cfg(include=[r"error"], redact=[r"\d+"])
        stages = stages_from_config(cfg)
        lines = ["info 123", "error 456"]
        result = list(run_pipeline(iter(lines), stages))
        assert result == ["error [REDACTED]"]

    def test_no_redact_stage_when_redact_empty(self):
        cfg = _cfg(redact=[])
        stages = stages_from_config(cfg)
        # No redaction stage means digit lines pass through unchanged
        lines = ["value 99"]
        assert list(run_pipeline(iter(lines), stages)) == ["value 99"]
