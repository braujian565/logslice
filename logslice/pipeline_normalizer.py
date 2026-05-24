"""Pipeline integration for the normalizer stage."""

from __future__ import annotations

from typing import Iterable, Iterator

from logslice.normalizer import normalize_lines


def _normalize_stage(
    lines: Iterable[str],
    *,
    ansi: bool,
    whitespace: bool,
    collapse: bool,
    control: bool,
    unicode_form: str | None,
    skip_empty: bool,
) -> Iterator[str]:
    yield from normalize_lines(
        lines,
        ansi=ansi,
        whitespace=whitespace,
        collapse=collapse,
        control=control,
        unicode_form=unicode_form,
        skip_empty=skip_empty,
    )


def apply_normalization_from_config(
    lines: Iterable[str],
    config: object,
) -> Iterator[str]:
    """Apply normalization to a line stream based on config flags.

    Expected config attributes (all optional, with defaults):
        normalize_ansi        (bool, default True)
        normalize_whitespace  (bool, default True)
        normalize_collapse    (bool, default True)
        normalize_control     (bool, default True)
        normalize_unicode     (str | None, default 'NFC')
        normalize_skip_empty  (bool, default False)
    """
    if not getattr(config, "normalize", False):
        yield from lines
        return

    yield from _normalize_stage(
        lines,
        ansi=getattr(config, "normalize_ansi", True),
        whitespace=getattr(config, "normalize_whitespace", True),
        collapse=getattr(config, "normalize_collapse", True),
        control=getattr(config, "normalize_control", True),
        unicode_form=getattr(config, "normalize_unicode", "NFC"),
        skip_empty=getattr(config, "normalize_skip_empty", False),
    )
