"""ANSI color highlighting for matched patterns in log lines."""

import re
from typing import Optional

ANSI_RESET = "\033[0m"
ANSI_COLORS = {
    "red":     "\033[31m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "blue":    "\033[34m",
    "magenta": "\033[35m",
    "cyan":    "\033[36m",
    "bold":    "\033[1m",
}

DEFAULT_HIGHLIGHT_COLOR = "yellow"


def highlight_match(line: str, pattern: re.Pattern, color: str = DEFAULT_HIGHLIGHT_COLOR) -> str:
    """Wrap all regex matches in a line with ANSI color codes."""
    ansi_start = ANSI_COLORS.get(color, ANSI_COLORS[DEFAULT_HIGHLIGHT_COLOR])

    def replacer(match: re.Match) -> str:
        return f"{ansi_start}{match.group(0)}{ANSI_RESET}"

    return pattern.sub(replacer, line)


def highlight_lines(
    lines: list[str],
    pattern: Optional[re.Pattern],
    color: str = DEFAULT_HIGHLIGHT_COLOR,
    enabled: bool = True,
) -> list[str]:
    """Apply highlighting to a list of lines if enabled and pattern is provided."""
    if not enabled or pattern is None:
        return lines
    return [highlight_match(line, pattern, color) for line in lines]


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape codes from a string."""
    ansi_escape = re.compile(r"\033\[[0-9;]*m")
    return ansi_escape.sub("", text)


def colorize(text: str, color: str) -> str:
    """Wrap arbitrary text in the given ANSI color."""
    ansi_start = ANSI_COLORS.get(color, ANSI_COLORS[DEFAULT_HIGHLIGHT_COLOR])
    return f"{ansi_start}{text}{ANSI_RESET}"


def available_colors() -> list[str]:
    """Return a sorted list of valid color names that can be used for highlighting."""
    return sorted(ANSI_COLORS.keys())
