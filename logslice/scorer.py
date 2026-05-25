"""Relevance scorer: assigns a numeric score to log lines based on weighted regex rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Tuple


@dataclass
class ScoredLine:
    line: str
    score: float
    line_number: int = 0

    def __str__(self) -> str:
        return self.line.rstrip("\n")


@dataclass
class ScoreRule:
    pattern: re.Pattern
    weight: float


def compile_score_rules(rules: List[Tuple[str, float]]) -> List[ScoreRule]:
    """Compile a list of (pattern, weight) pairs into ScoreRule objects."""
    if not rules:
        raise ValueError("At least one scoring rule is required")
    compiled = []
    for pattern, weight in rules:
        if not pattern:
            raise ValueError("Score rule pattern must not be empty")
        compiled.append(ScoreRule(pattern=re.compile(pattern), weight=float(weight)))
    return compiled


def score_line(line: str, rules: List[ScoreRule]) -> float:
    """Return the total score for a single line by summing weights of matching rules."""
    total = 0.0
    for rule in rules:
        if rule.pattern.search(line):
            total += rule.weight
    return total


def score_lines(
    lines: Iterable[str],
    rules: List[ScoreRule],
    *,
    min_score: float = 0.0,
) -> Iterator[ScoredLine]:
    """Yield ScoredLine objects for lines whose score meets min_score."""
    for lineno, line in enumerate(lines, start=1):
        s = score_line(line, rules)
        if s >= min_score:
            yield ScoredLine(line=line, score=s, line_number=lineno)


def top_scored(
    lines: Iterable[str],
    rules: List[ScoreRule],
    n: int = 10,
) -> List[ScoredLine]:
    """Return the top-n highest-scoring lines."""
    if n <= 0:
        raise ValueError("n must be a positive integer")
    scored = list(score_lines(lines, rules, min_score=float("-inf")))
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:n]
