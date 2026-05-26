"""Tests for logslice.summarizer."""
import pytest
from logslice.summarizer import (
    SummaryEntry,
    _normalize,
    summarize_lines,
    iter_unique_summaries,
    top_repeated,
)


class TestNormalize:
    def test_replaces_integers(self):
        assert _normalize("retries=3 timeout=10") == "retries=<N> timeout=<N>"

    def test_replaces_ip_address(self):
        assert _normalize("client 192.168.1.1 connected") == "client <IP> connected"

    def test_replaces_hex_string(self):
        assert _normalize("id=deadbeef1234abcd") == "id=<HEX>"

    def test_strips_trailing_newline(self):
        assert _normalize("hello\n") == "hello"

    def test_placeholders_false_keeps_original(self):
        result = _normalize("error code 42\n", placeholders=False)
        assert result == "error code 42"


class TestSummarizeLines:
    def test_single_line_returns_one_entry(self):
        entries = summarize_lines(["hello world\n"])
        assert len(entries) == 1
        assert entries[0].count == 1

    def test_duplicate_lines_grouped(self):
        lines = ["error: timeout\n"] * 5
        entries = summarize_lines(lines)
        assert len(entries) == 1
        assert entries[0].count == 5

    def test_different_numbers_grouped_together(self):
        lines = ["retry 1\n", "retry 2\n", "retry 3\n"]
        entries = summarize_lines(lines)
        assert len(entries) == 1
        assert entries[0].count == 3

    def test_distinct_patterns_separate_entries(self):
        lines = ["INFO started\n", "ERROR failed\n"]
        entries = summarize_lines(lines)
        assert len(entries) == 2

    def test_sorted_by_count_descending(self):
        lines = ["a\n"] * 3 + ["b\n"] * 7 + ["c\n"] * 1
        entries = summarize_lines(lines)
        assert entries[0].count == 7
        assert entries[-1].count == 1

    def test_min_count_filters_low_frequency(self):
        lines = ["rare\n"] + ["common\n"] * 4
        entries = summarize_lines(lines, min_count=2)
        assert all(e.count >= 2 for e in entries)

    def test_max_entries_limits_results(self):
        lines = [f"line {i}\n" for i in range(20)]
        entries = summarize_lines(lines, max_entries=5)
        assert len(entries) <= 5

    def test_line_numbers_tracked(self):
        lines = ["x\n", "y\n", "x\n"]
        entries = summarize_lines(lines, placeholders=False)
        x_entry = next(e for e in entries if e.sample == "x\n")
        assert x_entry.line_numbers == [1, 3]

    def test_empty_input_returns_empty(self):
        assert summarize_lines([]) == []

    def test_sample_preserves_original_line(self):
        lines = ["ERROR at 12:00:01 code=500\n"] * 2
        entries = summarize_lines(lines)
        assert entries[0].sample == "ERROR at 12:00:01 code=500\n"


class TestIterUniqueSummaries:
    def test_yields_one_per_pattern(self):
        lines = ["fail 1\n", "fail 2\n", "fail 3\n"]
        result = list(iter_unique_summaries(lines))
        assert len(result) == 1

    def test_distinct_lines_all_yielded(self):
        lines = ["alpha\n", "beta\n", "gamma\n"]
        result = list(iter_unique_summaries(lines))
        assert len(result) == 3

    def test_first_occurrence_is_kept(self):
        lines = ["val=10\n", "val=20\n"]
        result = list(iter_unique_summaries(lines))
        assert result[0] == "val=10\n"


class TestTopRepeated:
    def test_returns_only_repeated(self):
        lines = ["once\n"] + ["twice\n"] * 2
        entries = top_repeated(lines)
        assert all(e.count >= 2 for e in entries)

    def test_respects_n_limit(self):
        lines = [f"msg {i}\n" * (i + 2) for i in range(20)]
        flat = [l for group in lines for l in group]
        entries = top_repeated(flat, n=3)
        assert len(entries) <= 3

    def test_str_representation(self):
        entry = SummaryEntry(pattern="p", count=4, sample="hello\n")
        assert str(entry) == "[x4] hello"
