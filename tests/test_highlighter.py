"""Tests for logslice.highlighter module."""

import re
import pytest
from logslice.highlighter import (
    highlight_match,
    highlight_lines,
    strip_ansi,
    colorize,
    ANSI_RESET,
    ANSI_COLORS,
)


class TestHighlightMatch:
    def test_wraps_single_match(self):
        pattern = re.compile(r"ERROR")
        result = highlight_match("2024-01-01 ERROR something", pattern, "red")
        assert ANSI_COLORS["red"] in result
        assert ANSI_RESET in result
        assert "ERROR" in result

    def test_wraps_multiple_matches(self):
        pattern = re.compile(r"\d+")
        result = highlight_match("port 80 and 443", pattern, "cyan")
        assert result.count(ANSI_COLORS["cyan"]) == 2
        assert result.count(ANSI_RESET) == 2

    def test_no_match_returns_original(self):
        pattern = re.compile(r"CRITICAL")
        line = "INFO nothing special here"
        assert highlight_match(line, pattern) == line

    def test_unknown_color_falls_back_to_yellow(self):
        pattern = re.compile(r"foo")
        result = highlight_match("foo bar", pattern, "purple")
        assert ANSI_COLORS["yellow"] in result

    def test_preserves_surrounding_text(self):
        pattern = re.compile(r"WARN")
        result = highlight_match("prefix WARN suffix", pattern)
        clean = strip_ansi(result)
        assert clean == "prefix WARN suffix"


class TestHighlightLines:
    def test_highlights_all_matching_lines(self):
        pattern = re.compile(r"ERROR")
        lines = ["ERROR one", "INFO two", "ERROR three"]
        result = highlight_lines(lines, pattern)
        assert ANSI_COLORS["yellow"] in result[0]
        assert ANSI_COLORS["yellow"] not in result[1]
        assert ANSI_COLORS["yellow"] in result[2]

    def test_disabled_returns_original(self):
        pattern = re.compile(r"ERROR")
        lines = ["ERROR one", "ERROR two"]
        result = highlight_lines(lines, pattern, enabled=False)
        assert result == lines

    def test_none_pattern_returns_original(self):
        lines = ["line one", "line two"]
        result = highlight_lines(lines, None)
        assert result == lines


class TestStripAnsi:
    def test_removes_color_codes(self):
        colored = f"{ANSI_COLORS['red']}hello{ANSI_RESET}"
        assert strip_ansi(colored) == "hello"

    def test_plain_text_unchanged(self):
        assert strip_ansi("plain text") == "plain text"

    def test_multiple_codes_removed(self):
        text = f"{ANSI_COLORS['bold']}bold{ANSI_RESET} and {ANSI_COLORS['cyan']}cyan{ANSI_RESET}"
        assert strip_ansi(text) == "bold and cyan"


def test_colorize_wraps_text():
    result = colorize("MATCH", "green")
    assert result.startswith(ANSI_COLORS["green"])
    assert result.endswith(ANSI_RESET)
    assert "MATCH" in result
