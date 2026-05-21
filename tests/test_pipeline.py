"""Tests for logslice.pipeline."""

import pytest
from logslice.pipeline import (
    build_pipeline,
    run_pipeline,
    filter_stage,
    transform_stage,
    limit_stage,
    skip_stage,
)


LINES = ["alpha", "beta", "gamma", "delta", "epsilon"]


class TestBuildPipeline:
    def test_empty_stages_returns_all(self):
        result = list(run_pipeline(LINES, []))
        assert result == LINES

    def test_single_filter_stage(self):
        stage = filter_stage(lambda l: "a" in l)
        result = list(run_pipeline(LINES, [stage]))
        assert result == ["alpha", "beta", "gamma", "delta"]

    def test_two_filter_stages_compose(self):
        s1 = filter_stage(lambda l: "a" in l)
        s2 = filter_stage(lambda l: len(l) > 4)
        result = list(run_pipeline(LINES, [s1, s2]))
        assert result == ["alpha", "gamma", "delta"]

    def test_transform_stage_uppercases(self):
        stage = transform_stage(str.upper)
        result = list(run_pipeline(["hello", "world"], [stage]))
        assert result == ["HELLO", "WORLD"]

    def test_filter_then_transform(self):
        s1 = filter_stage(lambda l: l.startswith("a"))
        s2 = transform_stage(str.upper)
        result = list(run_pipeline(LINES, [s1, s2]))
        assert result == ["ALPHA"]


class TestLimitStage:
    def test_limit_fewer_than_total(self):
        result = list(run_pipeline(LINES, [limit_stage(3)]))
        assert result == ["alpha", "beta", "gamma"]

    def test_limit_more_than_total_returns_all(self):
        result = list(run_pipeline(LINES, [limit_stage(100)]))
        assert result == LINES

    def test_limit_zero_returns_nothing(self):
        result = list(run_pipeline(LINES, [limit_stage(0)]))
        assert result == []

    def test_limit_exactly_total(self):
        result = list(run_pipeline(LINES, [limit_stage(len(LINES))]))
        assert result == LINES


class TestSkipStage:
    def test_skip_first_two(self):
        result = list(run_pipeline(LINES, [skip_stage(2)]))
        assert result == ["gamma", "delta", "epsilon"]

    def test_skip_zero_returns_all(self):
        result = list(run_pipeline(LINES, [skip_stage(0)]))
        assert result == LINES

    def test_skip_all_returns_nothing(self):
        result = list(run_pipeline(LINES, [skip_stage(len(LINES))]))
        assert result == []

    def test_skip_more_than_total_returns_nothing(self):
        result = list(run_pipeline(LINES, [skip_stage(100)]))
        assert result == []


def test_combined_skip_limit_filter():
    lines = [str(i) for i in range(10)]  # "0" .. "9"
    s1 = skip_stage(2)          # "2" .. "9"
    s2 = limit_stage(5)         # "2" .. "6"
    s3 = filter_stage(lambda l: int(l) % 2 == 0)  # "2", "4", "6"
    result = list(run_pipeline(lines, [s1, s2, s3]))
    assert result == ["2", "4", "6"]


def test_run_pipeline_is_lazy():
    """Verify that run_pipeline does not consume the iterator eagerly."""
    consumed = []

    def tracking(lines):
        for line in lines:
            consumed.append(line)
            yield line

    pipeline = build_pipeline([tracking])
    gen = pipeline(iter(LINES))
    assert consumed == [], "pipeline should not consume lines before iteration"
    next(gen)
    assert len(consumed) == 1
