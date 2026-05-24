"""Pipeline integration for the log-line classifier."""

from __future__ import annotations

import re
from typing import Callable, Generator, Iterable, Optional

from logslice.classifier import (
    ClassifiedLine,
    classify_lines,
    compile_classifier_rules,
    preset_rules,
)
from logslice.config import LogSliceConfig


def _rules_from_config(
    cfg: LogSliceConfig,
) -> list[tuple[re.Pattern[str], str]]:
    """Build classifier rules from *cfg*.

    Looks for ``cfg.classifier_preset`` (str) and
    ``cfg.classifier_rules`` (list of [pattern, level] pairs).
    Falls back to the ``default`` preset when nothing is configured.
    """
    rules: list[tuple[str, str]] = []

    preset_name: Optional[str] = getattr(cfg, "classifier_preset", None)
    extra_rules: list = getattr(cfg, "classifier_rules", []) or []

    if preset_name:
        from logslice.classifier import _PRESETS

        raw = _PRESETS.get(preset_name, [])
        rules.extend(raw)
    else:
        from logslice.classifier import _PRESETS

        rules.extend(_PRESETS["default"])

    for entry in extra_rules:
        if isinstance(entry, (list, tuple)) and len(entry) == 2:
            rules.append((str(entry[0]), str(entry[1])))

    return compile_classifier_rules(rules)


def classification_stage(
    lines: Iterable[str],
    cfg: LogSliceConfig,
    callback: Optional[Callable[[ClassifiedLine], None]] = None,
) -> Generator[str, None, None]:
    """Classify each line and optionally invoke *callback*; yield lines unchanged."""
    rules = _rules_from_config(cfg)
    default_level: Optional[str] = getattr(cfg, "classifier_default_level", None)

    for cl in classify_lines(lines, rules, default_level=default_level):
        if callback is not None:
            callback(cl)
        yield cl.line


def apply_classification_from_config(
    lines: Iterable[str],
    cfg: LogSliceConfig,
    callback: Optional[Callable[[ClassifiedLine], None]] = None,
) -> Generator[str, None, None]:
    """Public entry-point used by the pipeline builder."""
    enabled: bool = getattr(cfg, "classify", False)
    if not enabled:
        yield from lines
        return
    yield from classification_stage(lines, cfg, callback=callback)
