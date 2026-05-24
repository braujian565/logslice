"""Alert rules: emit alerts when log lines match threshold conditions."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Generator, Iterable, List, Optional


@dataclass
class AlertRule:
    name: str
    pattern: str
    threshold: int = 1
    window: float = 60.0  # seconds
    _compiled: re.Pattern = field(init=False, repr=False)
    _hits: List[float] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Alert rule name must not be empty")
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")
        if self.window <= 0:
            raise ValueError("window must be > 0")
        self._compiled = re.compile(self.pattern)

    def record(self, line: str, ts: Optional[float] = None) -> bool:
        """Record a line hit; return True if the alert threshold is reached."""
        if not self._compiled.search(line):
            return False
        now = ts if ts is not None else time.monotonic()
        self._hits.append(now)
        # Evict hits outside the window
        cutoff = now - self.window
        self._hits = [h for h in self._hits if h >= cutoff]
        return len(self._hits) >= self.threshold

    def reset(self) -> None:
        self._hits.clear()


@dataclass
class Alert:
    rule_name: str
    line: str
    count: int
    window: float

    def __str__(self) -> str:
        return (
            f"[ALERT] {self.rule_name}: {self.count} match(es) "
            f"in {self.window}s window — {self.line.rstrip()}"
        )


def compile_alert_rules(rules: List[dict]) -> List[AlertRule]:
    """Build AlertRule objects from a list of config dicts."""
    return [
        AlertRule(
            name=r["name"],
            pattern=r["pattern"],
            threshold=r.get("threshold", 1),
            window=r.get("window", 60.0),
        )
        for r in rules
    ]


def check_alerts(
    lines: Iterable[str],
    rules: List[AlertRule],
    ts: Optional[float] = None,
) -> Generator[Alert, None, None]:
    """Yield Alert objects whenever a rule's threshold is crossed."""
    for line in lines:
        for rule in rules:
            if rule.record(line, ts=ts):
                yield Alert(
                    rule_name=rule.name,
                    line=line,
                    count=len(rule._hits),
                    window=rule.window,
                )
