"""Tests for logslice.rate_limiter."""

import pytest

from logslice.rate_limiter import RateLimiter, rate_limit_lines


class TestRateLimiterInit:
    def test_zero_max_lines_raises(self):
        with pytest.raises(ValueError, match="max_lines"):
            RateLimiter(max_lines=0)

    def test_negative_max_lines_raises(self):
        with pytest.raises(ValueError, match="max_lines"):
            RateLimiter(max_lines=-5)

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RateLimiter(max_lines=10, window_seconds=0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RateLimiter(max_lines=10, window_seconds=-1.0)


class TestRateLimiterAllow:
    def test_first_line_always_allowed(self):
        rl = RateLimiter(max_lines=1)
        assert rl.allow(now=0.0) is True

    def test_exceeding_limit_within_window_is_denied(self):
        rl = RateLimiter(max_lines=2, window_seconds=1.0)
        assert rl.allow(now=0.0) is True
        assert rl.allow(now=0.1) is True
        assert rl.allow(now=0.2) is False  # third line within 1 s window

    def test_line_allowed_after_window_expires(self):
        rl = RateLimiter(max_lines=1, window_seconds=1.0)
        assert rl.allow(now=0.0) is True
        assert rl.allow(now=0.5) is False   # still inside window
        assert rl.allow(now=1.01) is True   # window has rolled past first event

    def test_reset_clears_state(self):
        rl = RateLimiter(max_lines=1, window_seconds=1.0)
        rl.allow(now=0.0)  # fills the bucket
        rl.reset()
        assert rl.allow(now=0.1) is True  # bucket is empty again

    def test_large_burst_then_recovery(self):
        rl = RateLimiter(max_lines=3, window_seconds=1.0)
        for t in [0.0, 0.2, 0.4]:
            assert rl.allow(now=t) is True
        assert rl.allow(now=0.5) is False
        # After 1 s all three timestamps have expired
        assert rl.allow(now=1.1) is True


class TestRateLimitLines:
    def test_all_lines_pass_when_under_limit(self):
        lines = ["a", "b", "c"]
        result = list(rate_limit_lines(lines, max_lines=10, _clock=0.0))
        assert result == ["a", "b", "c"]

    def test_excess_lines_are_dropped(self):
        lines = ["line1", "line2", "line3", "line4", "line5"]
        result = list(rate_limit_lines(lines, max_lines=3, _clock=0.0))
        assert result == ["line1", "line2", "line3"]

    def test_empty_input_yields_nothing(self):
        result = list(rate_limit_lines([], max_lines=5, _clock=0.0))
        assert result == []

    def test_single_line_always_passes(self):
        result = list(rate_limit_lines(["only"], max_lines=1, _clock=0.0))
        assert result == ["only"]

    def test_invalid_max_lines_propagates(self):
        with pytest.raises(ValueError):
            list(rate_limit_lines(["x"], max_lines=0))
