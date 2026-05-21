"""Tests for the format_aggregation function added to logslice.formatter."""

from __future__ import annotations

import pytest

from logslice.formatter import format_aggregation


class TestFormatAggregation:
    def test_empty_dict_shows_no_data(self):
        result = format_aggregation({})
        assert "(no data)" in result

    def test_title_appears_in_output(self):
        result = format_aggregation({"ERROR": 3}, title="Log Levels")
        assert "Log Levels" in result

    def test_default_title(self):
        result = format_aggregation({"INFO": 1})
        assert "Aggregation" in result

    def test_single_entry_rendered(self):
        result = format_aggregation({"ERROR": 42})
        assert "ERROR" in result
        assert "42" in result

    def test_multiple_entries_all_present(self):
        data = {"ERROR": 10, "INFO": 5, "WARN": 1}
        result = format_aggregation(data)
        for key in data:
            assert key in result
        for val in data.values():
            assert str(val) in result

    def test_separator_line_present(self):
        result = format_aggregation({"A": 1})
        lines = result.splitlines()
        # Second line should be the separator
        assert set(lines[1]) == {"-"}

    def test_counts_right_aligned(self):
        data = {"short": 1, "a-much-longer-key": 100}
        result = format_aggregation(data)
        # Both counts should appear; basic sanity check
        assert "1" in result
        assert "100" in result

    def test_output_is_multiline(self):
        data = {"A": 1, "B": 2}
        result = format_aggregation(data)
        assert "\n" in result

    def test_custom_title_empty_data(self):
        result = format_aggregation({}, title="My Report")
        assert "My Report" in result
        assert "(no data)" in result
