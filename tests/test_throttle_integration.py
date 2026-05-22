"""Integration tests for Throttle used inside throttle_lines."""

from __future__ import annotations

import time

from logslice.throttle import Throttle, throttle_lines


def test_real_time_rate_limiting():
    """Emit 5 lines quickly; with max_lines=3 only 3 should pass."""
    throttle = Throttle(max_lines=3, window=10.0)
    lines = [f"line {i}" for i in range(5)]
    result = list(throttle_lines(lines, max_lines=3, _throttle=throttle))
    assert len(result) == 3
    assert result == ["line 0", "line 1", "line 2"]


def test_rate_resets_after_window():
    """After the window elapses the throttle should allow new lines."""
    window = 0.05  # 50 ms — fast enough for a test
    throttle = Throttle(max_lines=2, window=window)

    first_batch = ["a", "b", "c"]  # only 2 should pass
    passed_first = list(throttle_lines(first_batch, max_lines=2, _throttle=throttle))
    assert len(passed_first) == 2

    time.sleep(window + 0.02)

    second_batch = ["d", "e"]
    passed_second = list(throttle_lines(second_batch, max_lines=2, _throttle=throttle))
    assert len(passed_second) == 2


def test_high_volume_stream_respects_limit():
    """Simulate a high-volume stream and verify the cap is honoured."""
    max_lines = 10
    throttle = Throttle(max_lines=max_lines, window=60.0)
    big_stream = (f"log line {i}" for i in range(1000))
    result = list(throttle_lines(big_stream, max_lines=max_lines, _throttle=throttle))
    assert len(result) == max_lines
    assert result[0] == "log line 0"
    assert result[-1] == f"log line {max_lines - 1}"


def test_throttle_lines_preserves_content():
    """Lines that pass through must not be mutated."""
    lines = ["2024-01-01 ERROR something went wrong", "2024-01-01 INFO all good"]
    result = list(throttle_lines(lines, max_lines=100))
    assert result == lines
