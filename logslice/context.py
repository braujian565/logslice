"""Context window extraction: return N lines before/after each matching line."""

from typing import Iterator, List, Tuple
from collections import deque


def extract_context(
    lines: List[str],
    match_indices: List[int],
    before: int = 0,
    after: int = 0,
) -> Iterator[Tuple[int, str, bool]]:
    """Yield (line_index, line, is_match) tuples for matched lines plus context.

    Args:
        lines: All lines from the log source.
        match_indices: Zero-based indices of lines that matched a filter.
        before: Number of lines to include before each match.
        after: Number of lines to include after each match.

    Yields:
        Tuples of (original_line_index, line_text, is_match).
        Duplicate lines (overlapping context windows) are emitted only once.
    """
    if not match_indices:
        return

    emitted: set = set()
    total = len(lines)

    for idx in match_indices:
        start = max(0, idx - before)
        end = min(total - 1, idx + after)
        for i in range(start, end + 1):
            if i not in emitted:
                emitted.add(i)
                yield (i, lines[i], i == idx)


def collect_context_blocks(
    lines: List[str],
    match_indices: List[int],
    before: int = 0,
    after: int = 0,
) -> List[Tuple[int, str, bool]]:
    """Convenience wrapper returning a list instead of a generator."""
    return list(extract_context(lines, match_indices, before=before, after=after))


def group_into_blocks(
    context_tuples: List[Tuple[int, str, bool]]
) -> List[List[Tuple[int, str, bool]]]:
    """Split a flat context list into contiguous blocks separated by gaps."""
    if not context_tuples:
        return []

    blocks: List[List[Tuple[int, str, bool]]] = []
    current_block = [context_tuples[0]]

    for prev, curr in zip(context_tuples, context_tuples[1:]):
        if curr[0] == prev[0] + 1:
            current_block.append(curr)
        else:
            blocks.append(current_block)
            current_block = [curr]

    blocks.append(current_block)
    return blocks
