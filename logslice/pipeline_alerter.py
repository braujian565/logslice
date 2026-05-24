"""Pipeline integration for alert rules."""

from __future__ import annotations

from typing import Generator, Iterable, List

from logslice.alerter import Alert, AlertRule, compile_alert_rules, check_alerts
from logslice.alert_reporter import report_alerts


def _rules_from_config(cfg) -> List[AlertRule]:
    """Extract alert rules from a LogSliceConfig-like object."""
    raw = getattr(cfg, "alert_rules", None) or []
    return compile_alert_rules(raw)


def alert_stage(
    lines: Iterable[str],
    rules: List[AlertRule],
    on_alert=None,
) -> Generator[str, None, None]:
    """Pass-through stage that fires *on_alert* callback for each alert.

    Lines are always forwarded unchanged; alerts are side-effects.
    *on_alert* receives an :class:`~logslice.alerter.Alert` instance.
    """
    if not rules:
        yield from lines
        return

    for line in lines:
        triggered: List[Alert] = list(check_alerts([line], rules))
        if triggered and on_alert is not None:
            for alert in triggered:
                on_alert(alert)
        yield line


def apply_alerting_from_config(
    lines: Iterable[str],
    cfg,
    on_alert=None,
) -> Generator[str, None, None]:
    """Convenience wrapper: build rules from *cfg* and apply the alert stage."""
    rules = _rules_from_config(cfg)
    yield from alert_stage(lines, rules, on_alert=on_alert)
