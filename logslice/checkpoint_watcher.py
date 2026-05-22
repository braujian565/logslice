"""Combine checkpoint resumption with live tail / watch for continuous pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from logslice.checkpoint import (
    DEFAULT_CHECKPOINT_DIR,
    load_checkpoint,
    save_checkpoint,
)
from logslice.config import LogSliceConfig
from logslice.pipeline_builder import stages_from_config
from logslice.pipeline import run_pipeline


def resume_and_watch(
    log_path: str,
    cfg: LogSliceConfig,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
) -> Iterator[str]:
    """Yield filtered lines from *log_path*, starting at the last checkpoint.

    Unlike :func:`logslice.watch.watch` this function first drains any lines
    written since the previous run (using the saved byte offset) before
    entering live-tail mode.  The checkpoint is updated every time a new
    batch of lines is consumed.
    """
    stages = stages_from_config(cfg)

    # --- replay missed lines ---
    offset = load_checkpoint(log_path, checkpoint_dir) or 0
    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        fh.seek(offset)
        batch = fh.readlines()
        new_offset = fh.tell()

    if batch:
        yield from run_pipeline(iter(batch), stages)
        save_checkpoint(log_path, new_offset, checkpoint_dir)

    # --- live tail ---
    import time

    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        fh.seek(new_offset)
        while True:
            line = fh.readline()
            if line:
                filtered = list(run_pipeline(iter([line]), stages))
                for fl in filtered:
                    yield fl
                save_checkpoint(log_path, fh.tell(), checkpoint_dir)
            else:
                time.sleep(cfg.poll_interval if hasattr(cfg, "poll_interval") else 0.25)
