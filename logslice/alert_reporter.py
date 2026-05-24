"""Formatting helpers for Alert objects."""

from __future__ import annotations

import json
from typing import Callable, Iterable, List

from logslice.alerter import Alert


def format_alert_plain(alert: Alert) -> str:
    """Format an alert as a human-readable string."""
    return str(alert)


def format_alert_json(alert: Alert) -> str:
    """Format an alert as a JSON string."""
    return json.dumps(
        {
            "alert": True,
            "rule": alert.rule_name,
            "count": alert.count,
            "window": alert.window,
            "line": alert.line.rstrip(),
        }
    )


_FORMATTERS: dict[str, Callable[[Alert], str]] = {
    "plain": format_alert_plain,
    "json": format_alert_json,
}


def report_alerts(
    alerts: Iterable[Alert],
    fmt: str = "plain",
) -> List[str]:
    """Convert an iterable of alerts to formatted strings.

    Args:
        alerts: Iterable of Alert objects to format.
        fmt: Output format; one of 'plain' or 'json'. Defaults to 'plain'.

    Raises:
        ValueError: If an unsupported format is specified.

    Returns:
        A list of formatted alert strings.
    """
    if fmt not in _FORMATTERS:
        raise ValueError(
            f"Unsupported alert format {fmt!r}. Choose from: {', '.join(_FORMATTERS)}"
        )
    formatter = _FORMATTERS[fmt]
    return [formatter(a) for a in alerts]
