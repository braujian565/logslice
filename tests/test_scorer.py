"""Tests for logslice.scorer and logslice.pipeline_scorer."""

from __future__ import annotations

import pytest

from logslice.scorer import (
    ScoredLine,
    compile_score_rules,
    score_line,
    score_lines,
    top_scored,
)
from logslice.pipeline_scorer import apply_scoring_from_config, scoring_stage


# ---------------------------------------------------------------------------
# compile_score_rules
# ---------------------------------------------------------------------------

class TestCompileScoreRules:
    def test_returns_list_of_score_rules(self):
        rules = compile_score_rules([("ERROR", 2.0)])
        assert len(rules) == 1
        assert rules[0].weight == 2.0

    def test_empty_rules_raises(self):
        with pytest.raises(ValueError, match="At least one"):
            compile_score_rules([])

    def test_empty_pattern_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            compile_score_rules([(" ", 1.0), ("", 1.0)])

    def test_multiple_rules_compiled(self):
        rules = compile_score_rules([("WARN", 1.0), ("ERROR", 3.0)])
        assert len(rules) == 2


# ---------------------------------------------------------------------------
# score_line
# ---------------------------------------------------------------------------

class TestScoreLine:
    def test_no_match_returns_zero(self):
        rules = compile_score_rules([("ERROR", 5.0)])
        assert score_line("all good here", rules) == 0.0

    def test_single_match_returns_weight(self):
        rules = compile_score_rules([("ERROR", 5.0)])
        assert score_line("ERROR occurred", rules) == 5.0

    def test_multiple_rules_summed(self):
        rules = compile_score_rules([("ERROR", 3.0), ("critical", 2.0)])
        assert score_line("ERROR critical failure", rules) == 5.0

    def test_negative_weight_subtracts(self):
        rules = compile_score_rules([("DEBUG", -1.0), ("ERROR", 4.0)])
        assert score_line("DEBUG ERROR", rules) == 3.0


# ---------------------------------------------------------------------------
# score_lines
# ---------------------------------------------------------------------------

class TestScoreLines:
    def test_yields_scored_line_objects(self):
        rules = compile_score_rules([("ERROR", 1.0)])
        results = list(score_lines(["ERROR here\n", "ok\n"], rules, min_score=0.0))
        assert all(isinstance(r, ScoredLine) for r in results)

    def test_min_score_filters_low_scorers(self):
        rules = compile_score_rules([("ERROR", 1.0)])
        results = list(score_lines(["ERROR\n", "ok\n"], rules, min_score=1.0))
        assert len(results) == 1
        assert "ERROR" in results[0].line

    def test_line_numbers_assigned(self):
        rules = compile_score_rules([("x", 1.0)])
        results = list(score_lines(["x\n", "x\n", "x\n"], rules))
        assert [r.line_number for r in results] == [1, 2, 3]


# ---------------------------------------------------------------------------
# top_scored
# ---------------------------------------------------------------------------

class TestTopScored:
    def test_returns_n_highest(self):
        rules = compile_score_rules([("ERROR", 2.0), ("WARN", 1.0)])
        lines = ["ERROR WARN\n", "WARN only\n", "nothing\n", "ERROR only\n"]
        top = top_scored(lines, rules, n=2)
        assert len(top) == 2
        assert top[0].score >= top[1].score

    def test_zero_n_raises(self):
        rules = compile_score_rules([("x", 1.0)])
        with pytest.raises(ValueError):
            top_scored(["x\n"], rules, n=0)


# ---------------------------------------------------------------------------
# pipeline_scorer
# ---------------------------------------------------------------------------

def _cfg(**kwargs):
    class Cfg:
        score_rules = None
        min_score = 0.0
    c = Cfg()
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


class TestApplyScoringFromConfig:
    def test_no_rules_passes_all_lines(self):
        cfg = _cfg()
        result = list(apply_scoring_from_config(["a\n", "b\n"], cfg))
        assert result == ["a\n", "b\n"]

    def test_rules_filter_by_min_score(self):
        cfg = _cfg(score_rules=[("ERROR", 2.0)], min_score=1.0)
        lines = ["ERROR found\n", "all fine\n"]
        result = list(apply_scoring_from_config(lines, cfg))
        assert len(result) == 1
        assert "ERROR" in result[0]

    def test_scoring_stage_yields_scored_lines(self):
        cfg = _cfg(score_rules=[("WARN", 1.5)], min_score=0.0)
        results = list(scoring_stage(["WARN here\n", "ok\n"], cfg))
        assert isinstance(results[0], ScoredLine)
        assert results[0].score == 1.5
        assert results[1].score == 0.0

    def test_scoring_stage_no_rules_yields_zero_score(self):
        cfg = _cfg()
        results = list(scoring_stage(["line\n"], cfg))
        assert results[0].score == 0.0
