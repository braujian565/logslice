"""Pipeline integration for the tagger module."""

from __future__ import annotations

from typing import Generator, Iterable

from logslice.tagger import TaggedLine, compile_tag_rules, tag_line


def _rules_from_config(cfg) -> list[tuple]:
    """Extract and compile tag rules from a config object."""
    raw_rules = getattr(cfg, "tag_rules", None) or []
    if not raw_rules:
        return []
    return compile_tag_rules(raw_rules)


def tagging_stage(
    lines: Iterable[str],
    rules: list[tuple],
    stringify: bool = False,
) -> Generator[str | TaggedLine, None, None]:
    """Yield tagged lines; if stringify=True, yield str representations."""
    for line in lines:
        tagged = tag_line(line, rules)
        yield str(tagged) if stringify else tagged


def apply_tagging_from_config(
    lines: Iterable[str],
    cfg,
    stringify: bool = True,
) -> Generator[str | TaggedLine, None, None]:
    """Apply tagging pipeline stage driven by config.

    If no tag_rules are configured, lines pass through unchanged.
    """
    rules = _rules_from_config(cfg)
    if not rules:
        yield from lines
        return
    yield from tagging_stage(lines, rules, stringify=stringify)
