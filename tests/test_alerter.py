"""Tests for logslice.alerter."""

import pytest
from logslice.alerter import AlertRule, Alert, compile_alert_rules, check_alerts


class TestAlertRule:
    def test_match_below_threshold_returns_false(self):
        rule = AlertRule(name="err", pattern="ERROR", threshold=3, window=60)
        assert rule.record("ERROR happened") is False

    def test_match_at_threshold_returns_true(self):
        rule = AlertRule(name="err", pattern="ERROR", threshold=2, window=60)
        rule.record("ERROR one")
        assert rule.record("ERROR two") is True

    def test_non_matching_line_returns_false(self):
        rule = AlertRule(name="err", pattern="ERROR", threshold=1, window=60)
        assert rule.record("INFO all good") is False

    def test_reset_clears_hits(self):
        rule = AlertRule(name="err", pattern="ERROR", threshold=1, window=60)
        rule.record("ERROR")
        rule.reset()
        assert rule.record("ERROR") is True  # only 1 hit after reset

    def test_hits_outside_window_evicted(self):
        rule = AlertRule(name="err", pattern="ERROR", threshold=2, window=5.0)
        rule.record("ERROR", ts=0.0)   # old hit
        # Second hit is at t=10, window is 5 → first hit evicted
        result = rule.record("ERROR", ts=10.0)
        assert result is False  # only 1 hit in window

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            AlertRule(name="", pattern="ERROR")

    def test_zero_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            AlertRule(name="x", pattern=".", threshold=0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            AlertRule(name="x", pattern=".", window=-1)


class TestCompileAlertRules:
    def test_returns_list_of_rules(self):
        rules = compile_alert_rules([{"name": "a", "pattern": "ERR"}])
        assert len(rules) == 1
        assert isinstance(rules[0], AlertRule)

    def test_defaults_applied(self):
        rules = compile_alert_rules([{"name": "a", "pattern": "ERR"}])
        assert rules[0].threshold == 1
        assert rules[0].window == 60.0

    def test_empty_list_returns_empty(self):
        assert compile_alert_rules([]) == []


class TestCheckAlerts:
    def test_yields_alert_on_threshold(self):
        rule = AlertRule(name="err", pattern="ERROR", threshold=1, window=60)
        alerts = list(check_alerts(["ERROR found"], [rule]))
        assert len(alerts) == 1
        assert isinstance(alerts[0], Alert)
        assert alerts[0].rule_name == "err"

    def test_no_match_yields_nothing(self):
        rule = AlertRule(name="err", pattern="ERROR", threshold=1, window=60)
        alerts = list(check_alerts(["INFO ok"], [rule]))
        assert alerts == []

    def test_multiple_rules_can_both_fire(self):
        r1 = AlertRule(name="err", pattern="ERROR", threshold=1, window=60)
        r2 = AlertRule(name="crit", pattern="CRITICAL", threshold=1, window=60)
        alerts = list(check_alerts(["ERROR CRITICAL both"], [r1, r2]))
        names = {a.rule_name for a in alerts}
        assert names == {"err", "crit"}

    def test_alert_str_contains_rule_name(self):
        rule = AlertRule(name="myRule", pattern="FAIL", threshold=1, window=30)
        alerts = list(check_alerts(["FAIL here"], [rule]))
        assert "myRule" in str(alerts[0])
