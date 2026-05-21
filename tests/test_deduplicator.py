"""Tests for logslice.deduplicator."""

import pytest
from logslice.deduplicator import deduplicate_lines, count_duplicates, _line_key


LINES_NO_DUP = [
    "2024-01-01T00:00:01 INFO  started\n",
    "2024-01-01T00:00:02 DEBUG processing\n",
    "2024-01-01T00:00:03 ERROR failed\n",
]

LINES_WITH_DUP = [
    "2024-01-01T00:00:01 INFO  started\n",
    "2024-01-01T00:00:01 INFO  started\n",
    "2024-01-01T00:00:02 DEBUG processing\n",
    "2024-01-01T00:00:02 DEBUG processing\n",
    "2024-01-01T00:00:03 ERROR failed\n",
]


class TestDeduplicateLines:
    def test_no_duplicates_passes_all(self):
        result = list(deduplicate_lines(LINES_NO_DUP))
        assert result == LINES_NO_DUP

    def test_exact_duplicates_removed(self):
        result = list(deduplicate_lines(LINES_WITH_DUP))
        assert len(result) == 3
        assert result == LINES_NO_DUP

    def test_empty_input_yields_nothing(self):
        assert list(deduplicate_lines([])) == []

    def test_single_line_returned(self):
        assert list(deduplicate_lines(["hello\n"])) == ["hello\n"]

    def test_all_same_lines_yields_one(self):
        lines = ["same line\n"] * 10
        assert list(deduplicate_lines(lines)) == ["same line\n"]

    def test_ignore_timestamps_collapses_same_message(self):
        lines = [
            "2024-01-01T10:00:00 INFO  connected\n",
            "2024-01-01T10:00:01 INFO  connected\n",
            "2024-01-01T10:00:02 INFO  connected\n",
        ]
        result = list(deduplicate_lines(lines, ignore_timestamps=True))
        assert len(result) == 1

    def test_ignore_timestamps_keeps_different_messages(self):
        lines = [
            "2024-01-01T10:00:00 INFO  connected\n",
            "2024-01-01T10:00:01 INFO  disconnected\n",
        ]
        result = list(deduplicate_lines(lines, ignore_timestamps=True))
        assert len(result) == 2

    def test_max_cache_evicts_old_keys(self):
        # With max_cache=1 the first line's key is evicted after the second;
        # a repeat of the first line should then pass through again.
        lines = ["line A\n", "line B\n", "line A\n"]
        result = list(deduplicate_lines(lines, max_cache=1))
        # line A appears at position 0 and 2 (cache evicted after line B)
        assert result.count("line A\n") == 2
        assert result.count("line B\n") == 1

    def test_preserves_order(self):
        lines = ["c\n", "a\n", "b\n", "a\n", "c\n"]
        assert list(deduplicate_lines(lines)) == ["c\n", "a\n", "b\n"]


class TestCountDuplicates:
    def test_counts_exact_duplicates(self):
        counts = count_duplicates(LINES_WITH_DUP)
        values = list(counts.values())
        assert sorted(values) == [1, 2, 2]

    def test_no_duplicates_all_ones(self):
        counts = count_duplicates(LINES_NO_DUP)
        assert all(v == 1 for v in counts.values())

    def test_empty_returns_empty_dict(self):
        assert count_duplicates([]) == {}

    def test_ignore_timestamps_groups_by_message(self):
        lines = [
            "2024-01-01T10:00:00 INFO  ping\n",
            "2024-01-01T10:00:01 INFO  ping\n",
            "2024-01-01T10:00:02 INFO  ping\n",
        ]
        counts = count_duplicates(lines, ignore_timestamps=True)
        assert len(counts) == 1
        assert list(counts.values())[0] == 3


def test_line_key_strips_iso_timestamp():
    key_with = _line_key("2024-06-01T12:00:00Z ERROR boom", ignore_timestamps=True)
    key_plain = _line_key("ERROR boom", ignore_timestamps=True)
    assert key_with == key_plain


def test_line_key_no_strip_differs():
    key_with = _line_key("2024-06-01T12:00:00Z ERROR boom", ignore_timestamps=False)
    key_plain = _line_key("ERROR boom", ignore_timestamps=False)
    assert key_with != key_plain
