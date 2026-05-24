"""Line normalization: whitespace cleanup, encoding fixes, and line-ending standardization."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Iterator

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
_MULTI_SPACE = re.compile(r" {2,}")
_CTRL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def strip_ansi(line: str) -> str:
    """Remove ANSI escape sequences from a line."""
    return _ANSI_ESCAPE.sub("", line)


def normalize_whitespace(line: str, *, collapse: bool = True) -> str:
    """Strip leading/trailing whitespace and optionally collapse internal runs."""
    line = line.strip()
    if collapse:
        line = _MULTI_SPACE.sub(" ", line)
    return line


def strip_control_chars(line: str) -> str:
    """Remove non-printable control characters (keeps tab and newline)."""
    return _CTRL_CHARS.sub("", line)


def normalize_unicode(line: str, form: str = "NFC") -> str:
    """Apply Unicode normalization (NFC by default)."""
    return unicodedata.normalize(form, line)


def normalize_line(
    line: str,
    *,
    ansi: bool = True,
    whitespace: bool = True,
    collapse: bool = True,
    control: bool = True,
    unicode_form: str | None = "NFC",
) -> str:
    """Apply a configurable chain of normalization steps to a single line."""
    if ansi:
        line = strip_ansi(line)
    if control:
        line = strip_control_chars(line)
    if whitespace:
        line = normalize_whitespace(line, collapse=collapse)
    if unicode_form:
        line = normalize_unicode(line, form=unicode_form)
    return line


def normalize_lines(
    lines: Iterable[str],
    *,
    ansi: bool = True,
    whitespace: bool = True,
    collapse: bool = True,
    control: bool = True,
    unicode_form: str | None = "NFC",
    skip_empty: bool = False,
) -> Iterator[str]:
    """Normalize an iterable of lines, optionally skipping blank results."""
    for line in lines:
        result = normalize_line(
            line,
            ansi=ansi,
            whitespace=whitespace,
            collapse=collapse,
            control=control,
            unicode_form=unicode_form,
        )
        if skip_empty and not result:
            continue
        yield result
