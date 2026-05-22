"""Tests for logslice.checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logslice.checkpoint import (
    clear_checkpoint,
    load_checkpoint,
    read_from_checkpoint,
    save_checkpoint,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dir(tmp_path: Path) -> Path:
    d = tmp_path / "checkpoints"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------


class TestSaveLoadCheckpoint:
    def test_round_trip(self, tmp_path):
        d = _dir(tmp_path)
        save_checkpoint("/var/log/app.log", 1024, checkpoint_dir=d)
        assert load_checkpoint("/var/log/app.log", checkpoint_dir=d) == 1024

    def test_missing_returns_none(self, tmp_path):
        d = _dir(tmp_path)
        assert load_checkpoint("/no/such/file.log", checkpoint_dir=d) is None

    def test_overwrite_updates_offset(self, tmp_path):
        d = _dir(tmp_path)
        save_checkpoint("/var/log/app.log", 100, checkpoint_dir=d)
        save_checkpoint("/var/log/app.log", 999, checkpoint_dir=d)
        assert load_checkpoint("/var/log/app.log", checkpoint_dir=d) == 999

    def test_creates_checkpoint_dir(self, tmp_path):
        d = tmp_path / "nested" / "cp"
        save_checkpoint("/var/log/x.log", 0, checkpoint_dir=d)
        assert d.exists()

    def test_corrupt_file_returns_none(self, tmp_path):
        d = _dir(tmp_path)
        save_checkpoint("/var/log/app.log", 50, checkpoint_dir=d)
        # Corrupt the file
        from logslice.checkpoint import _checkpoint_path
        _checkpoint_path("/var/log/app.log", d).write_text("not json")
        assert load_checkpoint("/var/log/app.log", checkpoint_dir=d) is None


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------


class TestClearCheckpoint:
    def test_returns_true_when_existed(self, tmp_path):
        d = _dir(tmp_path)
        save_checkpoint("/var/log/app.log", 10, checkpoint_dir=d)
        assert clear_checkpoint("/var/log/app.log", checkpoint_dir=d) is True

    def test_returns_false_when_missing(self, tmp_path):
        d = _dir(tmp_path)
        assert clear_checkpoint("/var/log/app.log", checkpoint_dir=d) is False

    def test_file_removed_after_clear(self, tmp_path):
        d = _dir(tmp_path)
        save_checkpoint("/var/log/app.log", 10, checkpoint_dir=d)
        clear_checkpoint("/var/log/app.log", checkpoint_dir=d)
        assert load_checkpoint("/var/log/app.log", checkpoint_dir=d) is None


# ---------------------------------------------------------------------------
# read_from_checkpoint
# ---------------------------------------------------------------------------


class TestReadFromCheckpoint:
    def test_reads_all_lines_from_start(self, tmp_path):
        d = _dir(tmp_path)
        log = tmp_path / "app.log"
        log.write_text("line1\nline2\nline3\n")
        lines = list(read_from_checkpoint(str(log), checkpoint_dir=d))
        assert lines == ["line1\n", "line2\n", "line3\n"]

    def test_resumes_from_saved_offset(self, tmp_path):
        d = _dir(tmp_path)
        log = tmp_path / "app.log"
        log.write_text("line1\nline2\nline3\n")
        # First pass — consume everything
        list(read_from_checkpoint(str(log), checkpoint_dir=d))
        # Append new content
        with log.open("a") as fh:
            fh.write("line4\n")
        lines = list(read_from_checkpoint(str(log), checkpoint_dir=d))
        assert lines == ["line4\n"]

    def test_no_new_lines_yields_nothing(self, tmp_path):
        d = _dir(tmp_path)
        log = tmp_path / "app.log"
        log.write_text("hello\n")
        list(read_from_checkpoint(str(log), checkpoint_dir=d))
        lines = list(read_from_checkpoint(str(log), checkpoint_dir=d))
        assert lines == []

    def test_checkpoint_updated_after_read(self, tmp_path):
        d = _dir(tmp_path)
        log = tmp_path / "app.log"
        log.write_text("abc\n")
        list(read_from_checkpoint(str(log), checkpoint_dir=d))
        offset = load_checkpoint(str(log), checkpoint_dir=d)
        assert offset == log.stat().st_size
