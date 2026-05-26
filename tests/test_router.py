"""Tests for logslice.router."""

import pytest

from logslice.router import (
    RouteRule,
    compile_route_rules,
    route_line,
    route_lines,
    iter_routed,
)


# ---------------------------------------------------------------------------
# compile_route_rules
# ---------------------------------------------------------------------------

class TestCompileRouteRules:
    def test_returns_list_of_route_rules(self):
        rules = compile_route_rules([(r"ERROR", "errors")])
        assert len(rules) == 1
        assert isinstance(rules[0], RouteRule)

    def test_empty_rules_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            compile_route_rules([])

    def test_empty_destination_raises(self):
        with pytest.raises(ValueError, match="destination must not be empty"):
            compile_route_rules([(r"ERROR", "")])

    def test_multiple_rules_compiled(self):
        rules = compile_route_rules([(r"ERROR", "errors"), (r"WARN", "warnings")])
        assert len(rules) == 2
        assert rules[1].destination == "warnings"

    def test_pattern_is_compiled_regex(self):
        import re
        rules = compile_route_rules([(r"\d+", "numbers")])
        assert isinstance(rules[0].pattern, re.Pattern)


# ---------------------------------------------------------------------------
# route_line
# ---------------------------------------------------------------------------

class TestRouteLine:
    def _rules(self):
        return compile_route_rules([
            (r"ERROR", "errors"),
            (r"WARN", "warnings"),
        ])

    def test_matches_first_rule(self):
        result = route_line("2024-01-01 ERROR something broke", self._rules())
        assert result == ["errors"]

    def test_matches_second_rule(self):
        result = route_line("2024-01-01 WARN low disk", self._rules())
        assert result == ["warnings"]

    def test_no_match_returns_default(self):
        result = route_line("2024-01-01 INFO all good", self._rules())
        assert result == ["default"]

    def test_custom_default_key(self):
        result = route_line("INFO msg", self._rules(), default="misc")
        assert result == ["misc"]

    def test_stop_false_collects_all_matches(self):
        rules = compile_route_rules(
            [(r"ERROR", "errors"), (r"critical", "critical")], stop=False
        )
        result = route_line("ERROR critical failure", rules)
        assert "errors" in result
        assert "critical" in result


# ---------------------------------------------------------------------------
# route_lines
# ---------------------------------------------------------------------------

class TestRouteLines:
    def _rules(self):
        return compile_route_rules([
            (r"ERROR", "errors"),
            (r"WARN", "warnings"),
        ])

    def test_partitions_into_buckets(self):
        lines = ["ERROR bad", "WARN slow", "INFO ok"]
        buckets = route_lines(lines, self._rules())
        assert buckets["errors"] == ["ERROR bad"]
        assert buckets["warnings"] == ["WARN slow"]
        assert buckets["default"] == ["INFO ok"]

    def test_empty_input_returns_empty_dict(self):
        assert route_lines([], self._rules()) == {}

    def test_all_to_same_bucket(self):
        lines = ["ERROR a", "ERROR b"]
        buckets = route_lines(lines, self._rules())
        assert len(buckets["errors"]) == 2


# ---------------------------------------------------------------------------
# iter_routed
# ---------------------------------------------------------------------------

def test_iter_routed_yields_dest_line_pairs():
    rules = compile_route_rules([(r"ERROR", "errors")])
    pairs = list(iter_routed(["ERROR x", "INFO y"], rules))
    assert ("errors", "ERROR x") in pairs
    assert ("default", "INFO y") in pairs
