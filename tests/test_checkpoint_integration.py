"""Integration tests: checkpoint + slicer + pipeline working together."""

from __future__ import annotations

from pathlib import Path

from logslice.checkpoint import (
    clear_checkpoint,
    load_checkpoint,
    read_from_checkpoint,
    save_checkpoint,
)
from logslice.pipeline import run_pipeline
from logslice.pipeline_builder import stages_from_config
from logslice.config import LogSliceConfig


def _cfg(**kw) -> LogSliceConfig:
    base = dict(
        input=None, format="plain", highlight=False,
        include_patterns=[], exclude_patterns=[], start=None, end=None,
    )
    base.update(kw)
    return LogSliceConfig(**base)


def test_incremental_processing_across_runs(tmp_path):
    """Simulates two separate program runs; only new lines processed second time."""
    d = tmp_path / "cp"
    log = tmp_path / "service.log"
    log.write_text("run1 line1\nrun1 line2\n")

    # First run
    first_lines = list(read_from_checkpoint(str(log), checkpoint_dir=d))
    assert len(first_lines) == 2

    # Append more lines between runs
    with log.open("a") as fh:
        fh.write("run2 line1\nrun2 line2\nrun2 line3\n")

    # Second run — should only see new lines
    second_lines = list(read_from_checkpoint(str(log), checkpoint_dir=d))
    assert len(second_lines) == 3
    assert all("run2" in l for l in second_lines)


def test_checkpoint_with_pipeline_filter(tmp_path):
    """Lines read via checkpoint are correctly filtered by pipeline stages."""
    d = tmp_path / "cp"
    log = tmp_path / "app.log"
    log.write_text("INFO start\nERROR boom\nINFO end\n")

    raw = list(read_from_checkpoint(str(log), checkpoint_dir=d))
    cfg = _cfg(include_patterns=["ERROR"])
    stages = stages_from_config(cfg)
    filtered = list(run_pipeline(iter(raw), stages))

    assert filtered == ["ERROR boom\n"]


def test_clear_resets_to_beginning(tmp_path):
    """After clearing the checkpoint the full file is re-read."""
    d = tmp_path / "cp"
    log = tmp_path / "app.log"
    log.write_text("line1\nline2\n")

    list(read_from_checkpoint(str(log), checkpoint_dir=d))
    clear_checkpoint(str(log), checkpoint_dir=d)

    lines = list(read_from_checkpoint(str(log), checkpoint_dir=d))
    assert lines == ["line1\n", "line2\n"]


def test_empty_file_no_checkpoint_created(tmp_path):
    """Reading an empty file saves offset 0 but is still retrievable."""
    d = tmp_path / "cp"
    log = tmp_path / "empty.log"
    log.write_text("")

    lines = list(read_from_checkpoint(str(log), checkpoint_dir=d))
    assert lines == []
    assert load_checkpoint(str(log), checkpoint_dir=d) == 0
