"""Tests for logslice.pipeline_alerter."""

from types import SimpleNamespace
from logslice.alerter import AlertRule
from logslice.pipeline_alerter import alert_stage, apply_alerting_from_config


def _cfg(**kwargs):
    defaults = {"alert_rules": []}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestAlertStage:
    def test_passes_all_lines_through(self):
        rules = [AlertRule(name="e", pattern="ERROR", threshold=1, window=60)]
        lines = ["INFO ok", "ERROR bad", "DEBUG trace"]
        out = list(alert_stage(lines, rules))
        assert out == lines

    def test_callback_called_on_alert(self):
        rules = [AlertRule(name="e", pattern="ERROR", threshold=1, window=60)]
        fired = []
        list(alert_stage(["ERROR!"], rules, on_alert=fired.append))
        assert len(fired) == 1
        assert fired[0].rule_name == "e"

    def test_no_callback_does_not_raise(self):
        rules = [AlertRule(name="e", pattern="ERROR", threshold=1, window=60)]
        out = list(alert_stage(["ERROR!"], rules, on_alert=None))
        assert out == ["ERROR!"]

    def test_empty_rules_yields_all_lines(self):
        lines = ["a", "b", "c"]
        out = list(alert_stage(lines, []))
        assert out == lines

    def test_callback_not_called_below_threshold(self):
        rules = [AlertRule(name="e", pattern="ERROR", threshold=3, window=60)]
        fired = []
        list(alert_stage(["ERROR once", "INFO ok"], rules, on_alert=fired.append))
        assert fired == []


class TestApplyAlertingFromConfig:
    def test_no_rules_passes_through(self):
        cfg = _cfg(alert_rules=[])
        lines = ["hello", "world"]
        assert list(apply_alerting_from_config(lines, cfg)) == lines

    def test_rules_from_config_fire(self):
        cfg = _cfg(
            alert_rules=[{"name": "err", "pattern": "ERROR", "threshold": 1, "window": 60}]
        )
        fired = []
        list(apply_alerting_from_config(["ERROR!"], cfg, on_alert=fired.append))
        assert len(fired) == 1

    def test_missing_alert_rules_attr_treated_as_empty(self):
        cfg = SimpleNamespace()  # no alert_rules attribute
        lines = ["line1"]
        assert list(apply_alerting_from_config(lines, cfg)) == lines
