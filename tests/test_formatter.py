"""Tests for logslice.formatter."""

import json
from datetime import datetime

import pytest

from logslice.formatter import (
    format_line_plain,
    format_line_json,
    format_lines,
    format_summary,
)


class TestFormatLinePlain:
    def test_no_line_number(self):
        assert format_line_plain("hello world") == "hello world"

    def test_with_line_number(self):
        assert format_line_plain("hello world", line_number=5) == "5:hello world"

    def test_strips_nothing_extra(self):
        line = "2024-01-01 INFO starting"
        assert format_line_plain(line) == line


class TestFormatLineJson:
    def test_basic(self):
        out = json.loads(format_line_json("some log line"))
        assert out == {"line": "some log line"}

    def test_with_line_number(self):
        out = json.loads(format_line_json("msg", line_number=42))
        assert out["lineno"] == 42

    def test_with_timestamp(self):
        ts = datetime(2024, 3, 15, 12, 0, 0)
        out = json.loads(format_line_json("msg", timestamp=ts))
        assert out["timestamp"] == "2024-03-15T12:00:00"

    def test_strips_trailing_newline(self):
        out = json.loads(format_line_json("msg\n"))
        assert out["line"] == "msg"


class TestFormatSummary:
    def test_no_elapsed(self):
        s = format_summary(10, 100)
        assert "10" in s and "100" in s
        assert s.endswith(".")

    def test_with_elapsed(self):
        s = format_summary(5, 50, elapsed=0.123)
        assert "0.123s" in s


class TestFormatLines:
    LINES = [(1, "line one\n"), (2, "line two\n"), (3, "line three\n")]

    def test_plain_default(self):
        result = format_lines(self.LINES)
        assert result == ["line one", "line two", "line three"]

    def test_plain_with_line_numbers(self):
        result = format_lines(self.LINES, show_line_numbers=True)
        assert result[0] == "1:line one"
        assert result[2] == "3:line three"

    def test_json_format(self):
        result = format_lines(self.LINES, fmt="json")
        first = json.loads(result[0])
        assert first["line"] == "line one"
        assert "lineno" not in first

    def test_json_with_timestamps(self):
        ts = [datetime(2024, 1, i + 1) for i in range(3)]
        result = format_lines(self.LINES, fmt="json", timestamps=ts)
        assert json.loads(result[0])["timestamp"] == "2024-01-01T00:00:00"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Unknown format"):
            format_lines(self.LINES, fmt="xml")
