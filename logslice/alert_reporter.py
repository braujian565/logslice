"""Formatting helpers for Alert objects."""

from __future__ import annotations

import json
from typing import Iterable, List

from logslice.alerter import Alert


def format_alert_plain(alert: Alert) -> str:
    return str(alert)


def format_alert_json(alert: Alert) -> str:
    return json.dumps(
        {
            "alert": True,
            "rule": alert.rule_name,
            "count": alert.count,
            "window": alert.window,
            "line": alert.line.rstrip(),
        }
    )


def report_alerts(
    alerts: Iterable[Alert],
    fmt: str = "plain",
) -> List[str]:
    """Convert an iterable of alerts to formatted strings."""
    formatter = format_alert_json if fmt == "json" else format_alert_plain
    return [formatter(a) for a in alerts]
