"""Tests for logslice.transformer."""

from __future__ import annotations

import pytest

from logslice.transformer import (
    chain_transforms,
    make_lowercase,
    make_prefix,
    make_replace,
    make_strip,
    make_suffix,
    make_uppercase,
    transform_lines,
)


class TestMakeUppercase:
    def test_converts_to_upper(self):
        fn = make_uppercase()
        assert fn("hello world") == "HELLO WORLD"

    def test_already_upper_unchanged(self):
        fn = make_uppercase()
        assert fn("HELLO") == "HELLO"


class TestMakeLowercase:
    def test_converts_to_lower(self):
        fn = make_lowercase()
        assert fn("HELLO WORLD") == "hello world"

    def test_mixed_case(self):
        fn = make_lowercase()
        assert fn("HeLLo") == "hello"


class TestMakeStrip:
    def test_strips_whitespace(self):
        fn = make_strip()
        assert fn("  hello  ") == "hello"

    def test_strips_custom_chars(self):
        fn = make_strip("*")
        assert fn("***hello***") == "hello"

    def test_empty_string_unchanged(self):
        fn = make_strip()
        assert fn("") == ""


class TestMakePrefix:
    def test_prepends_string(self):
        fn = make_prefix("[INFO] ")
        assert fn("started") == "[INFO] started"

    def test_empty_prefix(self):
        fn = make_prefix("")
        assert fn("line") == "line"


class TestMakeSuffix:
    def test_appends_string(self):
        fn = make_suffix(" END")
        assert fn("line") == "line END"

    def test_empty_suffix(self):
        fn = make_suffix("")
        assert fn("line") == "line"


class TestMakeReplace:
    def test_replaces_pattern(self):
        fn = make_replace(r"\d+", "NUM")
        assert fn("error 404 on line 12") == "error NUM on line NUM"

    def test_no_match_unchanged(self):
        fn = make_replace(r"\d+", "NUM")
        assert fn("no digits here") == "no digits here"

    def test_case_insensitive_flag(self):
        import re
        fn = make_replace(r"error", "ERR", flags=re.IGNORECASE)
        assert fn("ERROR occurred") == "ERR occurred"


class TestChainTransforms:
    def test_applies_in_order(self):
        fn = chain_transforms(make_strip(), make_uppercase())
        assert fn("  hello  ") == "HELLO"

    def test_single_transform(self):
        fn = chain_transforms(make_prefix(">> "))
        assert fn("msg") == ">> msg"

    def test_empty_chain_returns_identity(self):
        fn = chain_transforms()
        assert fn("unchanged") == "unchanged"


class TestTransformLines:
    def test_applies_to_all_lines(self):
        lines = ["hello", "world"]
        result = list(transform_lines(lines, make_uppercase()))
        assert result == ["HELLO", "WORLD"]

    def test_empty_input_yields_nothing(self):
        result = list(transform_lines([], make_uppercase()))
        assert result == []

    def test_chained_transform_on_stream(self):
        fn = chain_transforms(make_strip(), make_prefix("- "))
        lines = ["  a  ", "  b  "]
        result = list(transform_lines(lines, fn))
        assert result == ["- a", "- b"]
