"""Redact sensitive patterns from log lines before output."""

import re
from typing import Iterable, Iterator, List, Tuple

# Built-in presets for common sensitive data patterns
PRESETS: dict[str, str] = {
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "email": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "credit_card": r"\b(?:\d[ \-]?){13,16}\b",
    "jwt": r"eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+",
    "api_key": r"(?i)(?:api[_\-]?key|token)[=:\s]+[\w\-]{16,}",
}


def compile_redaction_rules(
    patterns: List[str],
    replacement: str = "[REDACTED]",
) -> List[Tuple[re.Pattern, str]]:
    """Compile a list of regex pattern strings into (pattern, replacement) pairs."""
    rules = []
    for raw in patterns:
        preset = PRESETS.get(raw)
        compiled = re.compile(preset if preset is not None else raw)
        rules.append((compiled, replacement))
    return rules


def redact_line(
    line: str,
    rules: List[Tuple[re.Pattern, str]],
) -> str:
    """Apply all redaction rules to a single line and return the result."""
    for pattern, replacement in rules:
        line = pattern.sub(replacement, line)
    return line


def redact_lines(
    lines: Iterable[str],
    rules: List[Tuple[re.Pattern, str]],
) -> Iterator[str]:
    """Lazily apply redaction rules to each line in an iterable."""
    for line in lines:
        yield redact_line(line, rules)
