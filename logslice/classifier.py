"""Line classifier: assign severity levels to log lines via regex rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Generator, Iterable, Optional

# Built-in severity presets (pattern, level)
_PRESETS: dict[str, list[tuple[str, str]]] = {
    "default": [
        (r"\b(CRITICAL|FATAL)\b", "critical"),
        (r"\bERROR\b", "error"),
        (r"\bWARN(?:ING)?\b", "warning"),
        (r"\bINFO\b", "info"),
        (r"\bDEBUG\b", "debug"),
    ]
}


@dataclass
class ClassifiedLine:
    line: str
    level: Optional[str]
    lineno: int = 0


def compile_classifier_rules(
    rules: list[tuple[str, str]],
) -> list[tuple[re.Pattern[str], str]]:
    """Compile (pattern, level) pairs into (compiled_regex, level) pairs."""
    compiled: list[tuple[re.Pattern[str], str]] = []
    for pattern, level in rules:
        if not level:
            raise ValueError("Level must be a non-empty string.")
        compiled.append((re.compile(pattern, re.IGNORECASE), level))
    return compiled


def classify_line(
    line: str,
    rules: list[tuple[re.Pattern[str], str]],
    default_level: Optional[str] = None,
) -> Optional[str]:
    """Return the first matching severity level for *line*, or *default_level*."""
    for pattern, level in rules:
        if pattern.search(line):
            return level
    return default_level


def classify_lines(
    lines: Iterable[str],
    rules: list[tuple[re.Pattern[str], str]],
    default_level: Optional[str] = None,
    start: int = 1,
) -> Generator[ClassifiedLine, None, None]:
    """Yield :class:`ClassifiedLine` for every input line."""
    for lineno, line in enumerate(lines, start=start):
        level = classify_line(line, rules, default_level)
        yield ClassifiedLine(line=line, level=level, lineno=lineno)


def preset_rules(name: str = "default") -> list[tuple[re.Pattern[str], str]]:
    """Return compiled rules for a named preset."""
    if name not in _PRESETS:
        raise KeyError(f"Unknown classifier preset: {name!r}")
    return compile_classifier_rules(_PRESETS[name])
