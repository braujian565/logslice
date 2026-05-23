"""Build transformer pipeline stages from LogSliceConfig transform options."""

from __future__ import annotations

from typing import Callable, Iterable, Iterator, List

from logslice.transformer import (
    TransformFn,
    chain_transforms,
    make_lowercase,
    make_prefix,
    make_replace,
    make_strip,
    make_suffix,
    make_uppercase,
    transform_lines,
)


def _build_transforms(config: object) -> List[TransformFn]:
    """Extract transform functions declared in *config*.

    Recognised config attributes (all optional):
      - ``transform_uppercase`` (bool)
      - ``transform_lowercase`` (bool)
      - ``transform_strip`` (bool)
      - ``transform_prefix`` (str)
      - ``transform_suffix`` (str)
      - ``transform_replace`` (list of (pattern, replacement) tuples)
    """
    fns: List[TransformFn] = []

    if getattr(config, "transform_strip", False):
        fns.append(make_strip())

    if getattr(config, "transform_uppercase", False):
        fns.append(make_uppercase())
    elif getattr(config, "transform_lowercase", False):
        fns.append(make_lowercase())

    prefix = getattr(config, "transform_prefix", None)
    if prefix:
        fns.append(make_prefix(prefix))

    suffix = getattr(config, "transform_suffix", None)
    if suffix:
        fns.append(make_suffix(suffix))

    for pattern, replacement in getattr(config, "transform_replace", []) or []:
        fns.append(make_replace(pattern, replacement))

    return fns


def apply_transforms_from_config(
    lines: Iterable[str],
    config: object,
) -> Iterator[str]:
    """Apply all transforms declared in *config* to *lines*.

    If no transforms are configured the original lines are yielded unchanged.
    """
    fns = _build_transforms(config)
    if not fns:
        yield from lines
        return
    transform = chain_transforms(*fns)
    yield from transform_lines(lines, transform)
