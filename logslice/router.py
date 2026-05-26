"""Route log lines to different outputs based on pattern rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Generator, Iterable, List, Optional, Tuple


@dataclass
class RouteRule:
    """A single routing rule mapping a pattern to a destination key."""

    pattern: re.Pattern
    destination: str
    stop: bool = True  # stop checking further rules once matched


def compile_route_rules(
    rules: List[Tuple[str, str]],
    stop: bool = True,
    flags: int = 0,
) -> List[RouteRule]:
    """Compile a list of (pattern, destination) pairs into RouteRule objects."""
    if not rules:
        raise ValueError("route rules must not be empty")
    compiled = []
    for pattern, destination in rules:
        if not destination:
            raise ValueError("destination must not be empty")
        compiled.append(
            RouteRule(
                pattern=re.compile(pattern, flags),
                destination=destination,
                stop=stop,
            )
        )
    return compiled


def route_line(
    line: str,
    rules: List[RouteRule],
    default: str = "default",
) -> List[str]:
    """Return the list of destination keys for a single line."""
    destinations: List[str] = []
    for rule in rules:
        if rule.pattern.search(line):
            destinations.append(rule.destination)
            if rule.stop:
                return destinations
    if not destinations:
        return [default]
    return destinations


def route_lines(
    lines: Iterable[str],
    rules: List[RouteRule],
    default: str = "default",
) -> Dict[str, List[str]]:
    """Partition lines into buckets keyed by destination."""
    buckets: Dict[str, List[str]] = {}
    for line in lines:
        for dest in route_line(line, rules, default=default):
            buckets.setdefault(dest, []).append(line)
    return buckets


def iter_routed(
    lines: Iterable[str],
    rules: List[RouteRule],
    default: str = "default",
) -> Generator[Tuple[str, str], None, None]:
    """Yield (destination, line) pairs for each line."""
    for line in lines:
        for dest in route_line(line, rules, default=default):
            yield dest, line
