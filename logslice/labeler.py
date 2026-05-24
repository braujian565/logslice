"""Labeler: tag log lines with user-defined labels based on regex rules."""

from __future__ import annotations

import re
from typing import Generator, Iterable, List, Optional, Tuple

# A rule is (label, compiled_pattern)
LabelRule = Tuple[str, re.Pattern]


def compile_label_rules(rules: List[Tuple[str, str]]) -> List[LabelRule]:
    """Compile a list of (label, pattern_str) pairs into (label, Pattern) tuples.

    Raises ValueError for invalid regex patterns.
    """
    compiled: List[LabelRule] = []
    for label, pattern in rules:
        if not label:
            raise ValueError("Label must be a non-empty string.")
        try:
            compiled.append((label, re.compile(pattern)))
        except re.error as exc:
            raise ValueError(f"Invalid regex for label '{label}': {exc}") from exc
    return compiled


def label_line(line: str, rules: List[LabelRule]) -> Optional[str]:
    """Return the first matching label for *line*, or None if no rule matches."""
    for label, pattern in rules:
        if pattern.search(line):
            return label
    return None


def label_all(line: str, rules: List[LabelRule]) -> List[str]:
    """Return all matching labels for *line* (may be empty)."""
    return [label for label, pattern in rules if pattern.search(line)]


def label_lines(
    lines: Iterable[str],
    rules: List[LabelRule],
    default: Optional[str] = None,
    multi: bool = False,
) -> Generator[Tuple[str, List[str]], None, None]:
    """Yield (line, labels) pairs for each line.

    Args:
        lines:   Source lines.
        rules:   Compiled label rules.
        default: If given, attach this label when no rule matches.
        multi:   If True, collect all matching labels; otherwise stop at first.
    """
    for line in lines:
        if multi:
            labels = label_all(line, rules)
        else:
            first = label_line(line, rules)
            labels = [first] if first is not None else []

        if not labels and default is not None:
            labels = [default]

        yield line, labels
