"""High-level watcher: tail a file and apply the logslice pipeline."""

from __future__ import annotations

from typing import Callable, Iterator

from logslice.tail import tail_file
from logslice.pipeline import run_pipeline
from logslice.config import LogSliceConfig
from logslice.pipeline_builder import stages_from_config


def watch(
    config: LogSliceConfig,
    poll_interval: float = 0.2,
    max_wait: float | None = None,
    on_line: Callable[[str], None] | None = None,
) -> Iterator[str]:
    """Follow *config.input* and yield processed lines in real-time.

    Each new line appended to the file is passed through the pipeline
    defined by *config* (filters, transforms, etc.).

    Parameters
    ----------
    config:
        Fully populated :class:`~logslice.config.LogSliceConfig`.
    poll_interval:
        Seconds between file polls when idle.
    max_wait:
        Optional upper bound on total run time (handy for tests).
    on_line:
        Optional callback invoked for every emitted line (e.g. for
        side-effects like writing to a secondary sink).
    """
    if config.input is None:
        raise ValueError("config.input must be a file path for watch mode")

    stages = stages_from_config(config)

    raw_lines = tail_file(
        config.input,
        poll_interval=poll_interval,
        max_wait=max_wait,
    )

    for line in run_pipeline(raw_lines, stages):
        if on_line is not None:
            on_line(line)
        yield line
