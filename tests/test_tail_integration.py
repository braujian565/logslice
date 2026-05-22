"""Integration tests: tail_lines + tail_file together with real log data."""

import threading
import time

from logslice.tail import tail_file, tail_lines

_SAMPLE = "\n".join(
    [
        "2024-01-01T00:00:01 INFO  server started",
        "2024-01-01T00:00:02 DEBUG accepting connections",
        "2024-01-01T00:00:03 ERROR disk full",
        "2024-01-01T00:00:04 WARN  retrying",
        "2024-01-01T00:00:05 INFO  recovered",
    ]
)


def test_tail_lines_then_follow(tmp_path):
    """tail_lines gives historical context; tail_file then picks up new lines."""
    p = tmp_path / "server.log"
    p.write_text(_SAMPLE + "\n")

    # Historical snapshot
    history = tail_lines(str(p), n=2)
    assert history[-1] == "2024-01-01T00:00:05 INFO  recovered"
    assert len(history) == 2

    # Now follow for new content
    new_lines: list[str] = []

    def appender():
        time.sleep(0.05)
        with open(str(p), "a") as fh:
            fh.write("2024-01-01T00:00:06 INFO  new event\n")

    t = threading.Thread(target=appender, daemon=True)
    t.start()
    for line in tail_file(str(p), poll_interval=0.02, max_wait=0.4):
        new_lines.append(line)
    t.join()

    assert any("new event" in l for l in new_lines)
    # Old lines must NOT appear (seek to end on open)
    assert not any("server started" in l for l in new_lines)


def test_large_file_tail_lines(tmp_path):
    """tail_lines handles files larger than one read block."""
    p = tmp_path / "big.log"
    lines = [f"line {i:05d}" for i in range(5000)]
    p.write_text("\n".join(lines) + "\n")

    result = tail_lines(str(p), n=10)
    assert len(result) == 10
    assert result[-1] == "line 04999"
    assert result[0] == "line 04990"


def test_tail_lines_n_exceeds_file_length(tmp_path):
    """tail_lines returns all lines when n is greater than the total line count."""
    p = tmp_path / "short.log"
    p.write_text(_SAMPLE + "\n")

    result = tail_lines(str(p), n=100)
    assert len(result) == 5
    assert result[0] == "2024-01-01T00:00:01 INFO  server started"
    assert result[-1] == "2024-01-01T00:00:05 INFO  recovered"
