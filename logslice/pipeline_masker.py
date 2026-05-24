"""Wire masking into the processing pipeline via LogSliceConfig."""

from typing import Iterable, Iterator

from logslice.masker import compile_mask_rules, mask_lines


def _rules_from_config(cfg) -> list:
    """Extract mask rules from *cfg*, returning compiled rule tuples."""
    patterns = getattr(cfg, "mask_patterns", []) or []
    visible = getattr(cfg, "mask_visible_chars", 4)
    char = getattr(cfg, "mask_char", "*")
    if not patterns:
        return []
    return compile_mask_rules(patterns, visible=visible, char=char)


def apply_masking_from_config(
    lines: Iterable[str],
    cfg,
) -> Iterator[str]:
    """Apply configured masking rules to *lines*.

    If no mask patterns are configured the lines are yielded unchanged.
    """
    rules = _rules_from_config(cfg)
    if not rules:
        yield from lines
        return
    yield from mask_lines(lines, rules)
