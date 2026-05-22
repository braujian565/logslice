"""Tests for logslice.merger."""

from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pytest

from logslice.merger import merge_logs, merge_files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def lines(*args: str) -> list[str]:
    return list(args)


# ---------------------------------------------------------------------------
# merge_logs
# ---------------------------------------------------------------------------

class TestMergeLogs:
    def test_empty_sources_yields_nothing(self):
        result = list(merge_logs([]))
        assert result == []

    def test_single_source_returns_all_lines(self):
        src = ["2024-01-01 00:00:01 alpha", "2024-01-01 00:00:02 beta"]
        result = list(merge_logs([src]))
        assert result == src

    def test_two_sources_merged_in_order(self):
        a = ["2024-01-01 00:00:01 A", "2024-01-01 00:00:03 C"]
        b = ["2024-01-01 00:00:02 B", "2024-01-01 00:00:04 D"]
        result = list(merge_logs([a, b]))
        assert result == [
            "2024-01-01 00:00:01 A",
            "2024-01-01 00:00:02 B",
            "2024-01-01 00:00:03 C",
            "2024-01-01 00:00:04 D",
        ]

    def test_lines_without_timestamp_sort_last(self):
        a = ["2024-01-01 00:00:01 first", "no timestamp here"]
        b = ["2024-01-01 00:00:02 second"]
        result = list(merge_logs([a, b]))
        assert result[0] == "2024-01-01 00:00:01 first"
        assert result[1] == "2024-01-01 00:00:02 second"
        assert result[2] == "no timestamp here"

    def test_three_sources_interleaved(self):
        a = ["2024-01-01 00:00:01 A"]
        b = ["2024-01-01 00:00:02 B"]
        c = ["2024-01-01 00:00:00 C"]
        result = list(merge_logs([a, b, c]))
        assert result[0].endswith("C")
        assert result[1].endswith("A")
        assert result[2].endswith("B")

    def test_deduplicate_false_keeps_duplicates(self):
        shared = "2024-01-01 00:00:01 same"
        a = [shared]
        b = [shared]
        result = list(merge_logs([a, b], deduplicate=False))
        assert len(result) == 2

    def test_deduplicate_true_removes_consecutive_duplicates(self):
        shared = "2024-01-01 00:00:01 same"
        a = [shared]
        b = [shared]
        result = list(merge_logs([a, b], deduplicate=True))
        assert len(result) == 1
        assert result[0] == shared

    def test_one_empty_source_ignored(self):
        a = []
        b = ["2024-01-01 00:00:01 only"]
        result = list(merge_logs([a, b]))
        assert result == ["2024-01-01 00:00:01 only"]


# ---------------------------------------------------------------------------
# merge_files
# ---------------------------------------------------------------------------

class TestMergeFiles:
    def test_merges_two_files(self, tmp_path: Path):
        f1 = tmp_path / "a.log"
        f2 = tmp_path / "b.log"
        f1.write_text("2024-01-01 00:00:01 alpha\n2024-01-01 00:00:03 gamma\n")
        f2.write_text("2024-01-01 00:00:02 beta\n")
        result = list(merge_files([str(f1), str(f2)]))
        assert [l.split()[-1] for l in result] == ["alpha", "beta", "gamma"]

    def test_empty_file_list_yields_nothing(self):
        result = list(merge_files([]))
        assert result == []

    def test_single_file_returns_all_lines(self, tmp_path: Path):
        f = tmp_path / "only.log"
        f.write_text("2024-01-01 00:00:01 one\n2024-01-01 00:00:02 two\n")
        result = list(merge_files([str(f)]))
        assert len(result) == 2
