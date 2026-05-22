"""Tests for logslice.stats."""

from __future__ import annotations

import re

import pytest

from logslice.stats import LogStats, collect_stats


class TestLogStatsDefaults:
    def test_zero_total(self):
        s = LogStats()
        assert s.total_lines == 0

    def test_match_rate_zero_when_no_lines(self):
        s = LogStats()
        assert s.match_rate == 0.0

    def test_to_dict_keys(self):
        keys = LogStats().to_dict().keys()
        assert "total_lines" in keys
        assert "match_rate" in keys
        assert "level_counts" in keys


class TestCollectStats:
    def test_counts_all_lines(self):
        lines = ["a", "b", "c"]
        s = collect_stats(iter(lines))
        assert s.total_lines == 3

    def test_no_pattern_all_matched(self):
        lines = ["x", "y"]
        s = collect_stats(iter(lines))
        assert s.matched_lines == 2

    def test_pattern_filters_matched(self):
        lines = ["ERROR foo", "INFO bar", "ERROR baz"]
        pat = re.compile(r"ERROR")
        s = collect_stats(iter(lines), pattern=pat)
        assert s.matched_lines == 2

    def test_bytes_processed(self):
        lines = ["hello"]
        s = collect_stats(iter(lines))
        assert s.bytes_processed == 5

    def test_error_level_counted(self):
        lines = ["2024-01-01 ERROR something failed"]
        s = collect_stats(iter(lines))
        assert s.error_count == 1
        assert s.level_counts["ERROR"] == 1

    def test_warning_normalised(self):
        lines = ["WARN short form", "WARNING long form"]
        s = collect_stats(iter(lines))
        assert s.warning_count == 2
        assert s.level_counts.get("WARN", 0) == 0
        assert s.level_counts["WARNING"] == 2

    def test_critical_increments_error_count(self):
        lines = ["CRITICAL system down"]
        s = collect_stats(iter(lines))
        assert s.error_count == 1

    def test_match_rate_calculation(self):
        lines = ["ERROR a", "INFO b", "DEBUG c", "ERROR d"]
        pat = re.compile(r"ERROR")
        s = collect_stats(iter(lines), pattern=pat)
        assert abs(s.match_rate - 0.5) < 1e-9

    def test_empty_input(self):
        s = collect_stats(iter([]))
        assert s.total_lines == 0
        assert s.bytes_processed == 0
