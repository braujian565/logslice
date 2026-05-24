"""Tests for logslice.normalizer."""

from __future__ import annotations

import pytest

from logslice.normalizer import (
    normalize_line,
    normalize_lines,
    normalize_unicode,
    normalize_whitespace,
    strip_ansi,
    strip_control_chars,
)


class TestStripAnsi:
    def test_removes_color_codes(self):
        assert strip_ansi("\x1b[31mred\x1b[0m") == "red"

    def test_plain_text_unchanged(self):
        assert strip_ansi("hello world") == "hello world"

    def test_multiple_codes(self):
        assert strip_ansi("\x1b[1m\x1b[32mbold green\x1b[0m") == "bold green"

    def test_empty_string(self):
        assert strip_ansi("") == ""


class TestNormalizeWhitespace:
    def test_strips_leading_trailing(self):
        assert normalize_whitespace("  hello  ") == "hello"

    def test_collapses_internal_spaces(self):
        assert normalize_whitespace("foo   bar") == "foo bar"

    def test_no_collapse_preserves_internal(self):
        assert normalize_whitespace("foo   bar", collapse=False) == "foo   bar"

    def test_empty_string(self):
        assert normalize_whitespace("") == ""


class TestStripControlChars:
    def test_removes_null_byte(self):
        assert strip_control_chars("hel\x00lo") == "hello"

    def test_removes_bell(self):
        assert strip_control_chars("ring\x07bell") == "ringbell"

    def test_preserves_tab(self):
        assert strip_control_chars("col1\tcol2") == "col1\tcol2"

    def test_plain_text_unchanged(self):
        assert strip_control_chars("normal line") == "normal line"


class TestNormalizeUnicode:
    def test_nfc_composed(self):
        # e + combining acute -> single precomposed character
        decomposed = "e\u0301"
        result = normalize_unicode(decomposed, form="NFC")
        assert result == "\xe9"

    def test_nfd_decomposed(self):
        composed = "\xe9"
        result = normalize_unicode(composed, form="NFD")
        assert result == "e\u0301"


class TestNormalizeLine:
    def test_full_pipeline(self):
        raw = "  \x1b[32mINFO\x1b[0m   message\x00  "
        result = normalize_line(raw)
        assert result == "INFO message"

    def test_skip_ansi_step(self):
        line = "\x1b[31mred\x1b[0m"
        result = normalize_line(line, ansi=False)
        assert "\x1b" in result

    def test_skip_whitespace_step(self):
        result = normalize_line("  hello  ", whitespace=False)
        assert result == "  hello  "

    def test_skip_unicode_step(self):
        decomposed = "e\u0301"
        result = normalize_line(decomposed, unicode_form=None)
        assert result == decomposed


class TestNormalizeLines:
    def test_normalizes_all_lines(self):
        lines = ["  hello  ", "  world  "]
        result = list(normalize_lines(lines))
        assert result == ["hello", "world"]

    def test_skip_empty_removes_blank(self):
        lines = ["  ", "keep", "\x1b[0m"]
        result = list(normalize_lines(lines, skip_empty=True))
        assert result == ["keep"]

    def test_skip_empty_false_keeps_blank(self):
        lines = ["  ", "keep"]
        result = list(normalize_lines(lines, skip_empty=False))
        assert result == ["", "keep"]

    def test_empty_iterable(self):
        assert list(normalize_lines([])) == []
