"""Integrate labeling into the logslice pipeline via LogSliceConfig."""

from __future__ import annotations

from typing import Generator, Iterable, List, Tuple

from logslice.config import LogSliceConfig
from logslice.labeler import compile_label_rules, label_lines, LabelRule
from logslice.label_filter import drop_labeled, keep_labeled, prefix_label, strip_labels


def _build_rules(config: LogSliceConfig) -> List[LabelRule]:
    """Compile label rules stored in config.label_rules (list of [label, pattern])."""
    raw = getattr(config, "label_rules", None) or []
    return compile_label_rules([tuple(r) for r in raw])  # type: ignore[arg-type]


def apply_labeling(
    lines: Iterable[str],
    config: LogSliceConfig,
) -> Generator[str, None, None]:
    """Apply label rules from *config* to *lines* and yield processed strings.

    Behaviour is driven by config attributes:
      - label_rules:    list of [label, pattern] pairs.
      - label_keep:     if set, only lines matching these labels pass through.
      - label_drop:     if set, lines matching these labels are removed.
      - label_prefix:   if True, prepend the first label to each output line.
      - label_default:  fallback label for unmatched lines (optional).
      - label_multi:    if True, collect all matching labels per line.
    """
    rules = _build_rules(config)
    if not rules:
        yield from lines
        return

    default: str | None = getattr(config, "label_default", None)
    multi: bool = bool(getattr(config, "label_multi", False))
    keep: list = getattr(config, "label_keep", None) or []
    drop: list = getattr(config, "label_drop", None) or []
    do_prefix: bool = bool(getattr(config, "label_prefix", False))

    labeled = label_lines(lines, rules, default=default, multi=multi)

    if keep:
        labeled = keep_labeled(labeled, keep)
    if drop:
        labeled = drop_labeled(labeled, drop)

    if do_prefix:
        yield from prefix_label(labeled)
    else:
        yield from strip_labels(labeled)
