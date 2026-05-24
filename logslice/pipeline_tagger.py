"""Pipeline integration for the tagger module.

Builds tagging stages from LogSliceConfig and applies them
to a stream of lines, yielding TaggedLine objects.
"""

from __future__ import annotations

from typing import Generator, Iterable

from logslice.config import LogSliceConfig
from logslice.tagger import TaggedLine, compile_tag_rules, tag_line


def _rules_from_config(cfg: LogSliceConfig):
    """Extract and compile tag rules from *cfg*.

    Expects ``cfg.tag_rules`` to be a list of dicts with keys:
    - ``pattern`` (str): regex pattern to match against a line
    - ``tag``     (str): tag to apply when the pattern matches

    Returns an empty list when the attribute is absent or falsy.
    """
    raw = getattr(cfg, "tag_rules", None) or []
    if not raw:
        return []
    return compile_tag_rules([(r["pattern"], r["tag"]) for r in raw])


def tagging_stage(
    lines: Iterable[str],
    rules,
) -> Generator[TaggedLine, None, None]:
    """Apply *rules* to every line and yield :class:`~logslice.tagger.TaggedLine` objects.

    Lines that match no rule are still yielded as a TaggedLine with an
    empty tag set so that downstream stages receive a uniform type.

    Args:
        lines: Iterable of raw log lines.
        rules: Compiled tag rules as returned by :func:`compile_tag_rules`.

    Yields:
        :class:`TaggedLine` for every input line.
    """
    for line in lines:
        yield tag_line(line, rules)


def apply_tagging_from_config(
    lines: Iterable[str],
    cfg: LogSliceConfig,
) -> Generator[TaggedLine, None, None]:
    """Convenience wrapper that builds rules from *cfg* and runs the tagging stage.

    When no tag rules are configured the generator still yields every line
    wrapped in a :class:`TaggedLine` (with no tags attached), ensuring that
    callers always receive a homogeneous stream.

    Args:
        lines: Iterable of raw log lines.
        cfg:   Active :class:`~logslice.config.LogSliceConfig` instance.

    Yields:
        :class:`TaggedLine` for every input line.
    """
    rules = _rules_from_config(cfg)
    yield from tagging_stage(lines, rules)
