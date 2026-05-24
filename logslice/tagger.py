"""Tag log lines with key=value metadata based on regex patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Generator, Iterable


@dataclass
class TaggedLine:
    line: str
    tags: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        if not self.tags:
            return self.line
        tag_str = " ".join(f"{k}={v}" for k, v in sorted(self.tags.items()))
        return f"{self.line.rstrip()} [{tag_str}]"


def compile_tag_rules(
    rules: list[dict[str, str]]
) -> list[tuple[re.Pattern[str], str, str]]:
    """Compile a list of tag rule dicts into (pattern, key, value) triples.

    Each rule dict must have 'pattern', 'key', and 'value' keys.
    If 'value' is empty, the first capture group of the pattern is used.
    """
    compiled: list[tuple[re.Pattern[str], str, str]] = []
    for rule in rules:
        key = rule.get("key", "").strip()
        if not key:
            raise ValueError("Tag rule must have a non-empty 'key'.")
        pattern = rule.get("pattern", "")
        if not pattern:
            raise ValueError("Tag rule must have a non-empty 'pattern'.")
        compiled.append((re.compile(pattern), key, rule.get("value", "")))
    return compiled


def tag_line(
    line: str,
    rules: list[tuple[re.Pattern[str], str, str]],
) -> TaggedLine:
    """Apply compiled tag rules to a single line and return a TaggedLine."""
    tags: dict[str, str] = {}
    for pattern, key, value in rules:
        m = pattern.search(line)
        if m:
            if value:
                tags[key] = value
            else:
                groups = m.groups()
                tags[key] = groups[0] if groups else m.group(0)
    return TaggedLine(line=line, tags=tags)


def tag_lines(
    lines: Iterable[str],
    rules: list[tuple[re.Pattern[str], str, str]],
) -> Generator[TaggedLine, None, None]:
    """Yield TaggedLine objects for each input line."""
    for line in lines:
        yield tag_line(line, rules)
