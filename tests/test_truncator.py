"""Tests for logslice.truncator."""

from __future__ import annotations

import pytest

from logslice.truncator import (
    DEFAULT_MAX_LENGTH,
    DEFAULT_SUFFIX,
    count_truncated,
    truncate_line,
    truncate_lines,
)


class TestTruncateLine:
    def test_short_line_unchanged(self):
        line = "hello world"
        assert truncate_line(line, max_length=50) == line

    def test_exact_length_unchanged(self):
        line = "abcde"
        assert truncate_line(line, max_length=5) == line

    def test_long_line_truncated(self):
        line = "a" * 100
        result = truncate_line(line, max_length=20)
        assert len(result) == 20
        assert result.endswith(DEFAULT_SUFFIX)

    def test_custom_suffix_appended(self):
        line = "hello world"
        result = truncate_line(line, max_length=8, suffix=">>")
        assert result == "hello >"
        # length should equal max_length
        assert len(result) == 8

    def test_empty_suffix(self):
        line = "abcdefghij"
        result = truncate_line(line, max_length=5, suffix="")
        assert result == "abcde"

    def test_zero_max_length_raises(self):
        with pytest.raises(ValueError, match="max_length must be positive"):
            truncate_line("hello", max_length=0)

    def test_negative_max_length_raises(self):
        with pytest.raises(ValueError, match="max_length must be positive"):
            truncate_line("hello", max_length=-1)

    def test_suffix_longer_than_max_length_raises(self):
        with pytest.raises(ValueError, match="suffix length"):
            truncate_line("hello", max_length=2, suffix="...")

    def test_empty_line_unchanged(self):
        assert truncate_line("", max_length=10) == ""

    def test_default_max_length_used(self):
        short = "x" * 10
        assert truncate_line(short) == short
        long_line = "x" * (DEFAULT_MAX_LENGTH + 50)
        result = truncate_line(long_line)
        assert len(result) == DEFAULT_MAX_LENGTH
        assert result.endswith(DEFAULT_SUFFIX)


class TestTruncateLines:
    def test_all_short_lines_unchanged(self):
        lines = ["foo", "bar", "baz"]
        result = list(truncate_lines(lines, max_length=20))
        assert result == lines

    def test_long_lines_truncated(self):
        lines = ["a" * 200, "short", "b" * 150]
        result = list(truncate_lines(lines, max_length=50))
        assert len(result[0]) == 50
        assert result[1] == "short"
        assert len(result[2]) == 50

    def test_empty_iterable_yields_nothing(self):
        assert list(truncate_lines([], max_length=80)) == []

    def test_generator_input_consumed(self):
        def gen():
            yield "hello world"
            yield "x" * 100

        result = list(truncate_lines(gen(), max_length=10))
        assert len(result) == 2
        assert result[0] == "hello worl"


class TestCountTruncated:
    def test_none_exceed_limit(self):
        lines = ["short", "also short"]
        assert count_truncated(lines, max_length=50) == 0

    def test_all_exceed_limit(self):
        lines = ["a" * 100, "b" * 200]
        assert count_truncated(lines, max_length=50) == 2

    def test_some_exceed_limit(self):
        lines = ["tiny", "x" * 80, "ok", "y" * 60]
        assert count_truncated(lines, max_length=50) == 2

    def test_empty_input_returns_zero(self):
        assert count_truncated([], max_length=100) == 0
