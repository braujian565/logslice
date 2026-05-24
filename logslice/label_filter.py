"""Filter or route labeled lines produced by the labeler."""

from __future__ import annotations

from typing import Generator, Iterable, List, Optional, Tuple


def keep_labeled(
    labeled: Iterable[Tuple[str, List[str]]],
    keep: List[str],
) -> Generator[Tuple[str, List[str]], None, None]:
    """Yield only lines whose label list intersects *keep*."""
    keep_set = set(keep)
    for line, labels in labeled:
        if keep_set.intersection(labels):
            yield line, labels


def drop_labeled(
    labeled: Iterable[Tuple[str, List[str]]],
    drop: List[str],
) -> Generator[Tuple[str, List[str]], None, None]:
    """Yield lines whose label list does NOT intersect *drop*."""
    drop_set = set(drop)
    for line, labels in labeled:
        if not drop_set.intersection(labels):
            yield line, labels


def strip_labels(
    labeled: Iterable[Tuple[str, List[str]]],
) -> Generator[str, None, None]:
    """Discard label metadata and yield plain lines."""
    for line, _labels in labeled:
        yield line


def prefix_label(
    labeled: Iterable[Tuple[str, List[str]]],
    separator: str = " ",
) -> Generator[str, None, None]:
    """Prepend the first label (if any) to each line and yield the result."""
    for line, labels in labeled:
        if labels:
            yield f"[{labels[0]}]{separator}{line}"
        else:
            yield line
