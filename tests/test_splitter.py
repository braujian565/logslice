"""Tests for logslice.splitter."""

from __future__ import annotations

from pathlib import Path

import pytest

from logslice.splitter import iter_split, split_by_pattern, split_to_files


LINES = [
    "2024-01-01 ERROR something went wrong\n",
    "2024-01-01 INFO  startup complete\n",
    "2024-01-02 ERROR disk full\n",
    "2024-01-02 DEBUG verbose output\n",
    "no-level line\n",
]


class TestSplitByPattern:
    def test_full_match_key(self):
        result = split_by_pattern(LINES, r"ERROR|INFO|DEBUG")
        assert "ERROR" in result
        assert "INFO" in result
        assert "DEBUG" in result

    def test_unmatched_lines_stored_under_empty_key(self):
        result = split_by_pattern(LINES, r"ERROR|INFO|DEBUG")
        assert "" in result
        assert any("no-level" in ln for ln in result[""])

    def test_capture_group_key(self):
        result = split_by_pattern(LINES, r"(\d{4}-\d{2}-\d{2})", group=1)
        assert "2024-01-01" in result
        assert "2024-01-02" in result

    def test_empty_input_returns_empty_dict(self):
        result = split_by_pattern([], r"ERROR")
        assert result == {}

    def test_no_matches_all_under_empty_key(self):
        result = split_by_pattern(["hello\n", "world\n"], r"NOMATCH")
        assert list(result.keys()) == [""]
        assert len(result["")) == 2

    def test_line_count_preserved(self):
        result = split_by_pattern(LINES, r"ERROR|INFO|DEBUG")
        total = sum(len(v) for v in result.values())
        assert total == len(LINES)


class TestSplitToFiles:
    def test_creates_output_directory(self, tmp_path):
        out = tmp_path / "logs" / "split"
        split_to_files(LINES, r"ERROR|INFO|DEBUG", out)
        assert out.is_dir()

    def test_files_created_for_each_bucket(self, tmp_path):
        written = split_to_files(LINES, r"ERROR|INFO|DEBUG", tmp_path)
        assert "ERROR" in written
        assert written["ERROR"].exists()

    def test_unmatched_written_to_default_file(self, tmp_path):
        written = split_to_files(LINES, r"ERROR|INFO|DEBUG", tmp_path)
        assert "" in written
        assert written[""].name == "unmatched.log"

    def test_unmatched_discarded_when_name_is_none(self, tmp_path):
        written = split_to_files(
            LINES, r"ERROR|INFO|DEBUG", tmp_path, unmatched_name=None
        )
        assert "" not in written

    def test_file_content_matches_lines(self, tmp_path):
        written = split_to_files(LINES, r"ERROR|INFO|DEBUG", tmp_path)
        content = written["ERROR"].read_text()
        assert "something went wrong" in content
        assert "disk full" in content

    def test_prefix_applied_to_filename(self, tmp_path):
        written = split_to_files(
            LINES, r"ERROR|INFO|DEBUG", tmp_path, prefix="chunk"
        )
        assert written["ERROR"].name.startswith("chunk_")


class TestIterSplit:
    def test_yields_key_line_tuples(self):
        pairs = list(iter_split(LINES, r"ERROR|INFO|DEBUG"))
        assert len(pairs) == len(LINES)
        assert all(isinstance(k, str) and isinstance(ln, str) for k, ln in pairs)

    def test_unmatched_key_is_empty_string(self):
        pairs = list(iter_split(["no-level line\n"], r"ERROR"))
        assert pairs[0][0] == ""

    def test_capture_group_used_as_key(self):
        pairs = list(iter_split(["2024-01-01 ERROR\n"], r"(\d{4}-\d{2}-\d{2})", group=1))
        assert pairs[0][0] == "2024-01-01"
