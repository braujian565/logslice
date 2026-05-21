"""Pipeline: compose multiple log processing stages into a single pass."""

from typing import Callable, Iterable, Iterator, List


LineIterator = Iterator[str]
Stage = Callable[[LineIterator], LineIterator]


def build_pipeline(stages: List[Stage]) -> Stage:
    """Combine a list of stages into a single stage function.

    Each stage is a callable that accepts an iterator of lines and returns
    an iterator of lines.  Stages are applied left-to-right.
    """
    def pipeline(lines: LineIterator) -> LineIterator:
        result: LineIterator = iter(lines)
        for stage in stages:
            result = stage(result)
        return result

    return pipeline


def run_pipeline(
    lines: Iterable[str],
    stages: List[Stage],
) -> Iterator[str]:
    """Run *lines* through all *stages* and yield processed lines."""
    pipeline = build_pipeline(stages)
    yield from pipeline(iter(lines))


def filter_stage(predicate: Callable[[str], bool]) -> Stage:
    """Return a stage that keeps only lines for which *predicate* is True."""
    def stage(lines: LineIterator) -> LineIterator:
        return (line for line in lines if predicate(line))
    return stage


def transform_stage(transform: Callable[[str], str]) -> Stage:
    """Return a stage that applies *transform* to every line."""
    def stage(lines: LineIterator) -> LineIterator:
        return (transform(line) for line in lines)
    return stage


def limit_stage(max_lines: int) -> Stage:
    """Return a stage that stops after yielding *max_lines* lines."""
    def stage(lines: LineIterator) -> LineIterator:
        count = 0
        for line in lines:
            if count >= max_lines:
                break
            yield line
            count += 1
    return stage


def skip_stage(n: int) -> Stage:
    """Return a stage that skips the first *n* lines."""
    def stage(lines: LineIterator) -> LineIterator:
        skipped = 0
        for line in lines:
            if skipped < n:
                skipped += 1
                continue
            yield line
    return stage
