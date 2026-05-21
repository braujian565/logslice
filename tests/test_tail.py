"""Tests for logslice.tail."""

import os
import threading
import time
import tempfile

import pytest

from logslice.tail import tail_file, tail_lines


# ---------------------------------------------------------------------------
# tail_lines
# ---------------------------------------------------------------------------


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


class TestTailLines:
    def test_returns_last_n_lines(self, tmp_path):
        p = tmp_path / "log.txt"
        _write(str(p), "\n".join(str(i) for i in range(20)) + "\n")
        result = tail_lines(str(p), n=5)
        assert result == ["15", "16", "17", "18", "19"]

    def test_n_larger_than_file(self, tmp_path):
        p = tmp_path / "log.txt"
        _write(str(p), "a\nb\nc\n")
        result = tail_lines(str(p), n=100)
        assert result == ["a", "b", "c"]

    def test_n_zero_returns_empty(self, tmp_path):
        p = tmp_path / "log.txt"
        _write(str(p), "a\nb\n")
        assert tail_lines(str(p), n=0) == []

    def test_empty_file(self, tmp_path):
        p = tmp_path / "log.txt"
        p.write_text("")
        assert tail_lines(str(p), n=5) == []

    def test_single_line_no_newline(self, tmp_path):
        p = tmp_path / "log.txt"
        p.write_text("hello")
        result = tail_lines(str(p), n=3)
        assert result == ["hello"]


# ---------------------------------------------------------------------------
# tail_file (follow mode)
# ---------------------------------------------------------------------------


class TestTailFile:
    def test_yields_new_lines(self, tmp_path):
        p = tmp_path / "log.txt"
        p.write_text("")

        collected: list[str] = []

        def writer():
            time.sleep(0.05)
            with open(str(p), "a") as fh:
                fh.write("line1\nline2\n")

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        for line in tail_file(str(p), poll_interval=0.02, max_wait=0.5):
            collected.append(line)
        t.join()

        assert "line1" in collected
        assert "line2" in collected

    def test_max_wait_stops_iteration(self, tmp_path):
        p = tmp_path / "log.txt"
        p.write_text("")
        start = time.monotonic()
        lines = list(tail_file(str(p), poll_interval=0.05, max_wait=0.15))
        elapsed = time.monotonic() - start
        assert elapsed < 1.0
        assert lines == []

    def test_existing_content_not_replayed(self, tmp_path):
        p = tmp_path / "log.txt"
        p.write_text("old\n")
        lines = list(tail_file(str(p), poll_interval=0.05, max_wait=0.1))
        assert "old" not in lines
