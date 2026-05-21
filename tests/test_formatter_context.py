"""Tests for context-aware formatting in logslice.formatter."""

import json
import pytest
from logslice.formatter import format_context_block, format_context_separator


BLOCK = [
    (4, "before line\n", False),
    (5, "matched line\n", True),
    (6, "after line\n", False),
]


class TestFormatContextBlock:
    def test_plain_match_marker(self):
        output = list(format_context_block(BLOCK, fmt="plain"))
        assert output[1].startswith(">")

    def test_plain_context_marker(self):
        output = list(format_context_block(BLOCK, fmt="plain"))
        assert output[0].startswith(" ")
        assert output[2].startswith(" ")

    def test_plain_line_numbers_present(self):
        output = list(format_context_block(BLOCK, fmt="plain", show_numbers=True))
        assert "5:" in output[0]  # idx 4 -> line 5
        assert "6:" in output[1]
        assert "7:" in output[2]

    def test_plain_no_line_numbers(self):
        output = list(format_context_block(BLOCK, fmt="plain", show_numbers=False))
        for line in output:
            assert ":" not in line.split(" ", 1)[1].split(" ")[0]

    def test_plain_text_content(self):
        output = list(format_context_block(BLOCK, fmt="plain"))
        assert "matched line" in output[1]
        assert "before line" in output[0]

    def test_json_is_valid_json(self):
        output = list(format_context_block(BLOCK, fmt="json"))
        for item in output:
            parsed = json.loads(item)
            assert "line" in parsed

    def test_json_is_match_field(self):
        output = list(format_context_block(BLOCK, fmt="json"))
        parsed = [json.loads(o) for o in output]
        assert parsed[0]["is_match"] is False
        assert parsed[1]["is_match"] is True
        assert parsed[2]["is_match"] is False

    def test_json_line_numbers(self):
        output = list(format_context_block(BLOCK, fmt="json", show_numbers=True))
        parsed = [json.loads(o) for o in output]
        assert parsed[0]["line_number"] == 5
        assert parsed[1]["line_number"] == 6

    def test_custom_match_marker(self):
        output = list(
            format_context_block(BLOCK, fmt="plain", match_marker="*")
        )
        assert output[1].startswith("*")

    def test_empty_block_yields_nothing(self):
        output = list(format_context_block([], fmt="plain"))
        assert output == []

    def test_single_match_line(self):
        single = [(0, "only match\n", True)]
        output = list(format_context_block(single, fmt="plain"))
        assert len(output) == 1
        assert ">" in output[0]


class TestFormatContextSeparator:
    def test_returns_double_dash(self):
        assert format_context_separator() == "--"
