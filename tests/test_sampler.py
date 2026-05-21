"""Tests for logslice.sampler."""

import random
import pytest

from logslice.sampler import sample_by_rate, sample_reservoir, sample_every_nth


LINES = [f"line {i}\n" for i in range(100)]


# ---------------------------------------------------------------------------
# sample_by_rate
# ---------------------------------------------------------------------------

class TestSampleByRate:
    def test_rate_one_returns_all(self):
        result = list(sample_by_rate(LINES, 1.0))
        assert result == LINES

    def test_rate_zero_raises(self):
        with pytest.raises(ValueError, match="rate must be in"):
            list(sample_by_rate(LINES, 0.0))

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            list(sample_by_rate(LINES, -0.5))

    def test_rate_above_one_raises(self):
        with pytest.raises(ValueError):
            list(sample_by_rate(LINES, 1.1))

    def test_approximate_fraction(self):
        random.seed(42)
        result = list(sample_by_rate(LINES, 0.5))
        # With seed 42 and 100 lines we expect roughly 50 ± 20
        assert 20 <= len(result) <= 80

    def test_empty_input(self):
        assert list(sample_by_rate([], 0.5)) == []


# ---------------------------------------------------------------------------
# sample_reservoir
# ---------------------------------------------------------------------------

class TestSampleReservoir:
    def test_returns_k_lines(self):
        result = sample_reservoir(LINES, 10)
        assert len(result) == 10

    def test_all_results_are_from_input(self):
        result = sample_reservoir(LINES, 20)
        for line in result:
            assert line in LINES

    def test_fewer_lines_than_k(self):
        result = sample_reservoir(["a", "b", "c"], 10)
        assert sorted(result) == ["a", "b", "c"]

    def test_k_zero_raises(self):
        with pytest.raises(ValueError, match="positive integer"):
            sample_reservoir(LINES, 0)

    def test_k_negative_raises(self):
        with pytest.raises(ValueError):
            sample_reservoir(LINES, -1)

    def test_empty_input(self):
        assert sample_reservoir([], 5) == []

    def test_reproducible_with_seed(self):
        random.seed(0)
        r1 = sample_reservoir(LINES, 5)
        random.seed(0)
        r2 = sample_reservoir(LINES, 5)
        assert r1 == r2


# ---------------------------------------------------------------------------
# sample_every_nth
# ---------------------------------------------------------------------------

class TestSampleEveryNth:
    def test_n_one_returns_all(self):
        result = list(sample_every_nth(LINES, 1))
        assert result == LINES

    def test_n_two_returns_half(self):
        result = list(sample_every_nth(LINES, 2))
        assert result == LINES[::2]

    def test_n_ten(self):
        result = list(sample_every_nth(LINES, 10))
        assert len(result) == 10
        assert result[0] == LINES[0]
        assert result[1] == LINES[10]

    def test_n_zero_raises(self):
        with pytest.raises(ValueError, match=">= 1"):
            list(sample_every_nth(LINES, 0))

    def test_empty_input(self):
        assert list(sample_every_nth([], 5)) == []
