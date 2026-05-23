"""Line transformation utilities: uppercase, lowercase, strip, prefix, suffix, replace."""

from __future__ import annotations

import re
from typing import Callable, Iterable, Iterator


TransformFn = Callable[[str], str]


def make_uppercase() -> TransformFn:
    """Return a transform that converts lines to uppercase."""
    return str.upper


def make_lowercase() -> TransformFn:
    """Return a transform that converts lines to lowercase."""
    return str.lower


def make_strip(chars: str | None = None) -> TransformFn:
    """Return a transform that strips leading/trailing whitespace (or *chars*)."""
    def _strip(line: str) -> str:
        return line.strip(chars)
    return _strip


def make_prefix(prefix: str) -> TransformFn:
    """Return a transform that prepends *prefix* to every line."""
    def _prefix(line: str) -> str:
        return prefix + line
    return _prefix


def make_suffix(suffix: str) -> TransformFn:
    """Return a transform that appends *suffix* to every line."""
    def _suffix(line: str) -> str:
        return line + suffix
    return _suffix


def make_replace(pattern: str, replacement: str, flags: int = 0) -> TransformFn:
    """Return a transform that applies a regex substitution to every line."""
    compiled = re.compile(pattern, flags)

    def _replace(line: str) -> str:
        return compiled.sub(replacement, line)

    return _replace


def chain_transforms(*transforms: TransformFn) -> TransformFn:
    """Compose multiple transforms into a single function applied left-to-right."""
    def _chain(line: str) -> str:
        result = line
        for fn in transforms:
            result = fn(result)
        return result
    return _chain


def transform_lines(
    lines: Iterable[str],
    transform: TransformFn,
) -> Iterator[str]:
    """Apply *transform* to each line and yield the result."""
    for line in lines:
        yield transform(line)
