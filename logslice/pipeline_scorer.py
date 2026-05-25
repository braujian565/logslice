"""Pipeline integration for the relevance scorer."""

from __future__ import annotations

from typing import Iterable, Iterator, List, Tuple

from logslice.scorer import ScoredLine, compile_score_rules, score_lines


def _rules_from_config(cfg) -> List[Tuple[str, float]]:
    """Extract scoring rules from a config object.

    Expects cfg.score_rules to be a list of (pattern, weight) tuples,
    or an empty list / None if scoring is disabled.
    """
    return list(getattr(cfg, "score_rules", None) or [])


def _min_score_from_config(cfg) -> float:
    return float(getattr(cfg, "min_score", 0.0))


def apply_scoring_from_config(
    lines: Iterable[str],
    cfg,
) -> Iterator[str]:
    """Wrap lines through the scorer when rules are present.

    If no rules are configured the lines pass through unchanged.
    Lines that meet min_score are yielded as plain strings (score stripped).
    """
    raw_rules = _rules_from_config(cfg)
    if not raw_rules:
        yield from lines
        return

    rules = compile_score_rules(raw_rules)
    min_score = _min_score_from_config(cfg)
    for scored in score_lines(lines, rules, min_score=min_score):
        yield scored.line


def scoring_stage(
    lines: Iterable[str],
    cfg,
) -> Iterator[ScoredLine]:
    """Yield ScoredLine objects; useful when downstream needs the score value."""
    raw_rules = _rules_from_config(cfg)
    if not raw_rules:
        for lineno, line in enumerate(lines, start=1):
            yield ScoredLine(line=line, score=0.0, line_number=lineno)
        return

    rules = compile_score_rules(raw_rules)
    min_score = _min_score_from_config(cfg)
    yield from score_lines(lines, rules, min_score=min_score)
