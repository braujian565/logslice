"""Build pipeline stages from a LogSliceConfig, including redaction."""

from __future__ import annotations

import re
from typing import Callable, Iterator, List

from logslice.config import LogSliceConfig
from logslice.parser import extract_timestamp
from logslice.redactor import compile_redaction_rules, redact_lines

Stage = Callable[[Iterator[str]], Iterator[str]]


def _make_regex_filter(pattern: str, invert: bool = False) -> Stage:
    compiled = re.compile(pattern)

    def predicate(lines: Iterator[str]) -> Iterator[str]:
        for line in lines:
            matched = bool(compiled.search(line))
            if matched != invert:
                yield line

    return predicate


def _make_time_filter(
    start: str | None,
    end: str | None,
) -> Stage:
    from datetime import datetime

    fmt = "%Y-%m-%d %H:%M:%S"
    start_dt = datetime.strptime(start, fmt) if start else None
    end_dt = datetime.strptime(end, fmt) if end else None

    def predicate(lines: Iterator[str]) -> Iterator[str]:
        for line in lines:
            ts = extract_timestamp(line)
            if ts is None:
                yield line
                continue
            if start_dt and ts < start_dt:
                continue
            if end_dt and ts > end_dt:
                continue
            yield line

    return predicate


def _make_redaction_stage(cfg: LogSliceConfig) -> Stage | None:
    if not cfg.redact:
        return None
    rules = compile_redaction_rules(cfg.redact, replacement=cfg.redact_replacement)

    def stage(lines: Iterator[str]) -> Iterator[str]:
        return redact_lines(lines, rules)

    return stage


def stages_from_config(cfg: LogSliceConfig) -> List[Stage]:
    """Return ordered pipeline stages derived from *cfg*."""
    stages: List[Stage] = []

    for pattern in cfg.include:
        stages.append(_make_regex_filter(pattern, invert=False))
    for pattern in cfg.exclude:
        stages.append(_make_regex_filter(pattern, invert=True))

    if cfg.start_time or cfg.end_time:
        stages.append(_make_time_filter(cfg.start_time, cfg.end_time))

    redaction = _make_redaction_stage(cfg)
    if redaction is not None:
        stages.append(redaction)

    return stages
