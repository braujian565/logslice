"""Integration tests combining context extraction with formatting."""

import json
from logslice.context import collect_context_blocks, group_into_blocks
from logslice.formatter import (
    format_context_block,
    format_context_separator,
)

LINES = [f"entry {i}\n" for i in range(10)]


def test_extract_and_format_plain_two_blocks():
    """Two separate matches produce two blocks separated by '--'."""
    match_indices = [1, 7]
    tuples = collect_context_blocks(LINES, match_indices, before=1, after=1)
    blocks = group_into_blocks(tuples)
    assert len(blocks) == 2

    output_parts = []
    for i, block in enumerate(blocks):
        if i > 0:
            output_parts.append(format_context_separator())
        output_parts.extend(format_context_block(block, fmt="plain"))

    separator_count = output_parts.count("--")
    assert separator_count == 1


def test_extract_and_format_json_fields():
    """JSON output includes is_match and line_number for each context line."""
    match_indices = [5]
    tuples = collect_context_blocks(LINES, match_indices, before=2, after=2)
    blocks = group_into_blocks(tuples)
    assert len(blocks) == 1

    output = list(format_context_block(blocks[0], fmt="json", show_numbers=True))
    parsed = [json.loads(o) for o in output]

    match_entries = [p for p in parsed if p["is_match"]]
    context_entries = [p for p in parsed if not p["is_match"]]

    assert len(match_entries) == 1
    assert len(context_entries) == 4
    assert match_entries[0]["line_number"] == 6  # 0-indexed 5 -> 1-indexed 6


def test_adjacent_matches_form_single_block():
    """Adjacent matches with overlapping context merge into one block."""
    match_indices = [3, 4]
    tuples = collect_context_blocks(LINES, match_indices, before=1, after=1)
    blocks = group_into_blocks(tuples)
    assert len(blocks) == 1


def test_no_duplicates_in_output():
    """Context lines shared by two nearby matches appear only once."""
    match_indices = [2, 4]
    tuples = collect_context_blocks(LINES, match_indices, before=1, after=1)
    indices = [t[0] for t in tuples]
    assert len(indices) == len(set(indices))
