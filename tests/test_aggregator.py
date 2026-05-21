"""Tests for logslice.aggregator."""

from __future__ import annotations

import re

import pytest

from logslice.aggregator import aggregate_by_pattern, aggregate_by_time_bucket, top_n


LINES_WITH_LEVELS = [
    "2024-01-01 10:00:00 ERROR something broke",
    "2024-01-01 10:00:05 INFO  all good",
    "2024-01-01 10:00:10 ERROR disk full",
    "2024-01-01 10:00:15 WARN  low memory",
    "2024-01-01 10:00:20 ERROR timeout",
    "2024-01-01 10:00:25 INFO  startup",
]


class TestAggregateByPattern:
    def test_counts_full_match(self):
        pattern = re.compile(r"ERROR|INFO|WARN")
        result = aggregate_by_pattern(LINES_WITH_LEVELS, pattern)
        assert result["ERROR"] == 3
        assert result["INFO"] == 2
        assert result["WARN"] == 1

    def test_uses_capture_group(self):
        pattern = re.compile(r"(ERROR|INFO|WARN)")
        result = aggregate_by_pattern(LINES_WITH_LEVELS, pattern, group=1)
        assert result["ERROR"] == 3

    def test_no_matches_returns_empty(self):
        pattern = re.compile(r"CRITICAL")
        result = aggregate_by_pattern(LINES_WITH_LEVELS, pattern)
        assert result == {}

    def test_sorted_descending(self):
        pattern = re.compile(r"ERROR|INFO|WARN")
        result = aggregate_by_pattern(LINES_WITH_LEVELS, pattern)
        counts = list(result.values())
        assert counts == sorted(counts, reverse=True)

    def test_invalid_group_falls_back_to_full_match(self):
        pattern = re.compile(r"ERROR")
        # group=5 does not exist, should fall back to group 0
        result = aggregate_by_pattern(LINES_WITH_LEVELS, pattern, group=5)
        assert result["ERROR"] == 3

    def test_empty_input(self):
        pattern = re.compile(r"ERROR")
        result = aggregate_by_pattern([], pattern)
        assert result == {}


class TestAggregateByTimeBucket:
    def test_buckets_60_seconds(self):
        result = aggregate_by_time_bucket(LINES_WITH_LEVELS, bucket_seconds=60)
        # All lines fall in the same 60-second bucket
        assert len(result) == 1
        assert list(result.values())[0] == 6

    def test_buckets_10_seconds(self):
        result = aggregate_by_time_bucket(LINES_WITH_LEVELS, bucket_seconds=10)
        # Lines at :00, :05 share bucket :00; :10,:15 share :10; :20,:25 share :20
        assert sum(result.values()) == 6
        assert len(result) == 3

    def test_unknown_bucket_for_unparseable_lines(self):
        lines = ["no timestamp here", "also no timestamp"]
        result = aggregate_by_time_bucket(lines, bucket_seconds=60)
        assert result.get("__unknown__") == 2

    def test_zero_bucket_raises(self):
        with pytest.raises(ValueError):
            aggregate_by_time_bucket(LINES_WITH_LEVELS, bucket_seconds=0)

    def test_negative_bucket_raises(self):
        with pytest.raises(ValueError):
            aggregate_by_time_bucket(LINES_WITH_LEVELS, bucket_seconds=-5)

    def test_empty_input(self):
        result = aggregate_by_time_bucket([], bucket_seconds=60)
        assert result == {}


class TestTopN:
    def test_returns_top_n(self):
        data = {"a": 10, "b": 5, "c": 1}
        assert top_n(data, 2) == {"a": 10, "b": 5}

    def test_n_larger_than_data(self):
        data = {"a": 3}
        assert top_n(data, 10) == {"a": 3}

    def test_zero_n_raises(self):
        with pytest.raises(ValueError):
            top_n({"a": 1}, 0)

    def test_negative_n_raises(self):
        with pytest.raises(ValueError):
            top_n({"a": 1}, -1)
