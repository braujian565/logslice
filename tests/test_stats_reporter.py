"""Tests for logslice.stats_reporter."""

from __future__ import annotations

import json
from collections import Counter

import pytest

from logslice.stats import LogStats
from logslice.stats_reporter import format_stats_json, format_stats_plain, report_stats


def _sample_stats(**kwargs) -> LogStats:
    defaults = dict(
        total_lines=100,
        matched_lines=40,
        bytes_processed=4096,
        level_counts=Counter({"ERROR": 5, "INFO": 35}),
        error_count=5,
        warning_count=0,
    )
    defaults.update(kwargs)
    s = LogStats()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


class TestFormatStatsPlain:
    def test_title_present(self):
        out = format_stats_plain(_sample_stats(), title="My Report")
        assert "My Report" in out

    def test_total_lines_shown(self):
        out = format_stats_plain(_sample_stats(total_lines=42))
        assert "42" in out

    def test_match_rate_shown(self):
        out = format_stats_plain(_sample_stats(total_lines=10, matched_lines=5))
        assert "50.0%" in out

    def test_level_breakdown_shown(self):
        out = format_stats_plain(_sample_stats())
        assert "ERROR" in out
        assert "INFO" in out

    def test_empty_levels_no_breakdown_header(self):
        s = _sample_stats(level_counts=Counter())
        out = format_stats_plain(s)
        assert "Level breakdown" not in out


class TestFormatStatsJson:
    def test_valid_json(self):
        out = format_stats_json(_sample_stats())
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_contains_total_lines(self):
        out = format_stats_json(_sample_stats(total_lines=77))
        data = json.loads(out)
        assert data["total_lines"] == 77

    def test_level_counts_serialised(self):
        out = format_stats_json(_sample_stats())
        data = json.loads(out)
        assert data["level_counts"]["ERROR"] == 5


class TestReportStats:
    def test_plain_format(self):
        out = report_stats(_sample_stats(), fmt="plain")
        assert "Total lines" in out

    def test_json_format(self):
        out = report_stats(_sample_stats(), fmt="json")
        json.loads(out)  # must not raise

    def test_default_is_plain(self):
        out = report_stats(_sample_stats())
        assert "Total lines" in out
