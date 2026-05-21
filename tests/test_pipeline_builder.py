"""Tests for logslice.pipeline_builder."""

from datetime import datetime
from unittest.mock import MagicMock

from logslice.pipeline import run_pipeline
from logslice.pipeline_builder import stages_from_config


def _cfg(**kwargs):
    """Create a minimal mock LogSliceConfig with sensible defaults."""
    cfg = MagicMock()
    cfg.start_time = kwargs.get("start_time", None)
    cfg.end_time = kwargs.get("end_time", None)
    cfg.filters = kwargs.get("filters", [])
    cfg.exclude_filters = kwargs.get("exclude_filters", [])
    cfg.skip = kwargs.get("skip", 0)
    cfg.max_lines = kwargs.get("max_lines", 0)
    return cfg


LINES = [
    "2024-01-01 10:00:00 INFO  service started",
    "2024-01-01 10:01:00 ERROR disk full",
    "2024-01-01 10:02:00 INFO  request ok",
    "2024-01-01 10:03:00 WARN  high memory",
    "2024-01-01 10:04:00 ERROR timeout",
]


class TestStagesFromConfig:
    def test_no_filters_returns_all(self):
        cfg = _cfg()
        result = list(run_pipeline(LINES, stages_from_config(cfg)))
        assert result == LINES

    def test_include_filter_keeps_matching(self):
        cfg = _cfg(filters=["ERROR"])
        result = list(run_pipeline(LINES, stages_from_config(cfg)))
        assert all("ERROR" in l for l in result)
        assert len(result) == 2

    def test_exclude_filter_removes_matching(self):
        cfg = _cfg(exclude_filters=["ERROR"])
        result = list(run_pipeline(LINES, stages_from_config(cfg)))
        assert all("ERROR" not in l for l in result)
        assert len(result) == 3

    def test_include_and_exclude_combine(self):
        cfg = _cfg(filters=["10:0"], exclude_filters=["ERROR"])
        result = list(run_pipeline(LINES, stages_from_config(cfg)))
        assert len(result) == 3
        assert all("ERROR" not in l for l in result)

    def test_max_lines_limits_output(self):
        cfg = _cfg(max_lines=2)
        result = list(run_pipeline(LINES, stages_from_config(cfg)))
        assert result == LINES[:2]

    def test_skip_removes_first_n(self):
        cfg = _cfg(skip=2)
        result = list(run_pipeline(LINES, stages_from_config(cfg)))
        assert result == LINES[2:]

    def test_skip_and_limit_combine(self):
        cfg = _cfg(skip=1, max_lines=2)
        result = list(run_pipeline(LINES, stages_from_config(cfg)))
        assert result == LINES[1:3]

    def test_zero_skip_and_limit_ignored(self):
        cfg = _cfg(skip=0, max_lines=0)
        result = list(run_pipeline(LINES, stages_from_config(cfg)))
        assert result == LINES

    def test_multiple_include_filters_narrow_results(self):
        cfg = _cfg(filters=["ERROR", "disk"])
        result = list(run_pipeline(LINES, stages_from_config(cfg)))
        assert result == ["2024-01-01 10:01:00 ERROR disk full"]
