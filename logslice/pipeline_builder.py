"""High-level helpers to assemble a standard logslice pipeline from config."""

import re
from typing import List

from logslice.config import LogSliceConfig
from logslice.parser import matches_filter, extract_timestamp
from logslice.pipeline import (
    Stage,
    filter_stage,
    transform_stage,
    limit_stage,
    skip_stage,
)


def _make_regex_filter(pattern: str, invert: bool) -> Stage:
    compiled = re.compile(pattern)

    def predicate(line: str) -> bool:
        matched = bool(compiled.search(line))
        return (not matched) if invert else matched

    return filter_stage(predicate)


def _make_time_filter(start=None, end=None) -> Stage:
    def predicate(line: str) -> bool:
        ts = extract_timestamp(line)
        if ts is None:
            return True  # pass lines with no parseable timestamp
        if start and ts < start:
            return False
        if end and ts > end:
            return False
        return True

    return filter_stage(predicate)


def stages_from_config(cfg: LogSliceConfig) -> List[Stage]:
    """Build an ordered list of pipeline stages from *cfg*."""
    stages: List[Stage] = []

    # Time-range filter comes first so regex stages see fewer lines
    if cfg.start_time or cfg.end_time:
        stages.append(_make_time_filter(cfg.start_time, cfg.end_time))

    # Include-pattern filters
    for pat in (cfg.filters or []):
        stages.append(_make_regex_filter(pat, invert=False))

    # Exclude-pattern filters
    for pat in (cfg.exclude_filters or []):
        stages.append(_make_regex_filter(pat, invert=True))

    # Skip / limit
    if cfg.skip and cfg.skip > 0:
        stages.append(skip_stage(cfg.skip))
    if cfg.max_lines and cfg.max_lines > 0:
        stages.append(limit_stage(cfg.max_lines))

    return stages
