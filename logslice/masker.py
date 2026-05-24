"""Field masking: partially obscure sensitive values in log lines."""

import re
from typing import Iterable, Iterator, List, Tuple

# Built-in mask presets
PRESETS: dict[str, str] = {
    "credit_card": r"\b(?:\d[ -]?){13,15}\d\b",
    "email": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "bearer_token": r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}


def _build_mask(value: str, visible: int, char: str) -> str:
    """Return *value* with all but the last *visible* chars replaced by *char*."""
    if visible <= 0 or visible >= len(value):
        return char * max(len(value), 4)
    return char * (len(value) - visible) + value[-visible:]


def compile_mask_rules(
    patterns: List[str],
    visible: int = 4,
    char: str = "*",
) -> List[Tuple[re.Pattern, int, str]]:
    """Compile a list of pattern strings (or preset names) into mask rule tuples."""
    rules: List[Tuple[re.Pattern, int, str]] = []
    for pat in patterns:
        resolved = PRESETS.get(pat, pat)
        rules.append((re.compile(resolved), visible, char))
    return rules


def mask_line(
    line: str,
    rules: List[Tuple[re.Pattern, int, str]],
) -> str:
    """Apply all mask rules to *line*, returning the masked result."""
    for pattern, visible, char in rules:
        def _replace(m: re.Match, v: int = visible, c: str = char) -> str:
            return _build_mask(m.group(0), v, c)
        line = pattern.sub(_replace, line)
    return line


def mask_lines(
    lines: Iterable[str],
    rules: List[Tuple[re.Pattern, int, str]],
) -> Iterator[str]:
    """Yield each line with mask rules applied."""
    for line in lines:
        yield mask_line(line, rules)
