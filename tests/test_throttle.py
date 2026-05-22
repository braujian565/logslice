"""Tests for logslice.throttle."""

from __future__ import annotations

import pytest

from logslice.throttle import Throttle, throttle_lines


# ---------------------------------------------------------------------------
# Throttle unit tests
# ---------------------------------------------------------------------------

class TestThrottleInit:
    def test_zero_max_lines_raises(self):
        with pytest.raises(ValueError, match="max_lines"):
            Throttle(0)

    def test_negative_max_lines_raises(self):
        with pytest.raises(ValueError, match="max_lines"):
            Throttle(-1)

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            Throttle(10, window=0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            Throttle(10, window=-0.5)


class TestThrottleAllow:
    def test_allows_up_to_max_lines(self):
        t = Throttle(3, window=1.0)
        now = 100.0
        results = [t.allow(now) for _ in range(5)]
        assert results == [True, True, True, False, False]

    def test_allows_again_after_window_expires(self):
        t = Throttle(2, window=1.0)
        assert t.allow(100.0) is True
        assert t.allow(100.0) is True
        assert t.allow(100.0) is False
        # advance past the window
        assert t.allow(101.1) is True

    def test_reset_clears_state(self):
        t = Throttle(1, window=1.0)
        t.allow(100.0)
        assert t.allow(100.0) is False
        t.reset()
        assert t.allow(100.0) is True

    def test_allow_uses_monotonic_by_default(self):
        """Smoke test: calling without explicit now should not raise."""
        t = Throttle(100, window=1.0)
        assert t.allow() is True


# ---------------------------------------------------------------------------
# throttle_lines tests
# ---------------------------------------------------------------------------

class TestThrottleLines:
    def _make_throttle(self, allowed: list[bool]) -> Throttle:
        """Stub throttle whose allow() returns values from a list."""
        class _Stub(Throttle):
            def __init__(self):
                self._answers = iter(allowed)

            def allow(self, now=None):
                return next(self._answers)

        return _Stub()

    def test_passes_allowed_lines(self):
        stub = self._make_throttle([True, False, True, False, True])
        lines = ["a", "b", "c", "d", "e"]
        result = list(throttle_lines(lines, max_lines=3, _throttle=stub))
        assert result == ["a", "c", "e"]

    def test_empty_input_yields_nothing(self):
        result = list(throttle_lines([], max_lines=5))
        assert result == []

    def test_all_blocked_yields_nothing(self):
        stub = self._make_throttle([False, False, False])
        result = list(throttle_lines(["x", "y", "z"], max_lines=1, _throttle=stub))
        assert result == []

    def test_creates_throttle_if_not_provided(self):
        lines = ["line1", "line2", "line3"]
        # With max_lines=10 all lines should pass in a single burst
        result = list(throttle_lines(lines, max_lines=10))
        assert result == lines
