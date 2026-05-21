"""Tests for logslice.watch."""

import threading
import time

import pytest

from logslice.config import LogSliceConfig
from logslice.watch import watch


def _cfg(**kwargs) -> LogSliceConfig:
    defaults = dict(
        input=None,
        format="plain",
        highlight=False,
        include_patterns=[],
        exclude_patterns=[],
        start=None,
        end=None,
    )
    defaults.update(kwargs)
    return LogSliceConfig(**defaults)


class TestWatch:
    def test_yields_new_lines(self, tmp_path):
        p = tmp_path / "app.log"
        p.write_text("")
        cfg = _cfg(input=str(p))

        collected: list[str] = []

        def writer():
            time.sleep(0.05)
            with open(str(p), "a") as fh:
                fh.write("hello world\n")

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        for line in watch(cfg, poll_interval=0.02, max_wait=0.5):
            collected.append(line)
        t.join()

        assert "hello world" in collected

    def test_include_filter_applied(self, tmp_path):
        p = tmp_path / "app.log"
        p.write_text("")
        cfg = _cfg(input=str(p), include_patterns=["ERROR"])

        collected: list[str] = []

        def writer():
            time.sleep(0.05)
            with open(str(p), "a") as fh:
                fh.write("INFO startup\nERROR boom\n")

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        for line in watch(cfg, poll_interval=0.02, max_wait=0.5):
            collected.append(line)
        t.join()

        assert all("ERROR" in l for l in collected)
        assert not any("INFO" in l for l in collected)

    def test_on_line_callback_called(self, tmp_path):
        p = tmp_path / "app.log"
        p.write_text("")
        cfg = _cfg(input=str(p))
        side_effects: list[str] = []

        def writer():
            time.sleep(0.05)
            with open(str(p), "a") as fh:
                fh.write("ping\n")

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        for _ in watch(
            cfg,
            poll_interval=0.02,
            max_wait=0.5,
            on_line=side_effects.append,
        ):
            pass
        t.join()

        assert "ping" in side_effects

    def test_no_input_raises(self):
        cfg = _cfg(input=None)
        with pytest.raises(ValueError, match="config.input"):
            list(watch(cfg, max_wait=0.0))
