"""Tests for logslice.context module."""

import pytest
from logslice.context import extract_context, collect_context_blocks, group_into_blocks

LINES = [
    "line 0\n",
    "line 1\n",
    "line 2\n",
    "line 3\n",
    "line 4\n",
    "line 5\n",
    "line 6\n",
]


class TestExtractContext:
    def test_no_matches_yields_nothing(self):
        result = collect_context_blocks(LINES, [], before=2, after=2)
        assert result == []

    def test_match_only_no_context(self):
        result = collect_context_blocks(LINES, [3], before=0, after=0)
        assert result == [(3, "line 3\n", True)]

    def test_before_context(self):
        result = collect_context_blocks(LINES, [3], before=2, after=0)
        assert [r[0] for r in result] == [1, 2, 3]
        assert result[-1][2] is True
        assert result[0][2] is False

    def test_after_context(self):
        result = collect_context_blocks(LINES, [3], before=0, after=2)
        assert [r[0] for r in result] == [3, 4, 5]

    def test_before_and_after(self):
        result = collect_context_blocks(LINES, [3], before=1, after=1)
        assert [r[0] for r in result] == [2, 3, 4]

    def test_clamps_to_start_of_file(self):
        result = collect_context_blocks(LINES, [0], before=5, after=0)
        assert [r[0] for r in result] == [0]

    def test_clamps_to_end_of_file(self):
        result = collect_context_blocks(LINES, [6], before=0, after=5)
        assert [r[0] for r in result] == [6]

    def test_overlapping_windows_deduplicated(self):
        result = collect_context_blocks(LINES, [2, 4], before=1, after=1)
        indices = [r[0] for r in result]
        assert len(indices) == len(set(indices)), "Duplicate indices found"
        assert indices == sorted(indices)

    def test_match_flag_correct(self):
        result = collect_context_blocks(LINES, [2], before=1, after=1)
        flags = {r[0]: r[2] for r in result}
        assert flags[1] is False
        assert flags[2] is True
        assert flags[3] is False

    def test_multiple_matches_all_marked(self):
        result = collect_context_blocks(LINES, [1, 5], before=0, after=0)
        assert all(r[2] is True for r in result)


class TestGroupIntoBlocks:
    def test_empty_input(self):
        assert group_into_blocks([]) == []

    def test_single_block(self):
        tuples = [(0, "a", True), (1, "b", False), (2, "c", False)]
        blocks = group_into_blocks(tuples)
        assert len(blocks) == 1
        assert blocks[0] == tuples

    def test_two_separate_blocks(self):
        tuples = [(0, "a", True), (2, "b", True)]
        blocks = group_into_blocks(tuples)
        assert len(blocks) == 2

    def test_block_contents_preserved(self):
        tuples = [(1, "x", False), (2, "y", True), (5, "z", True)]
        blocks = group_into_blocks(tuples)
        assert blocks[0] == [(1, "x", False), (2, "y", True)]
        assert blocks[1] == [(5, "z", True)]
