"""Export processed log data to various output formats.

Supports exporting to CSV, NDJSON (newline-delimited JSON), and plain text,
with optional field extraction via regex capture groups.
"""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Dict, Iterable, Iterator, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Field extraction helpers
# ---------------------------------------------------------------------------

def extract_fields(
    line: str,
    pattern: re.Pattern,
    field_names: Optional[List[str]] = None,
) -> Optional[Dict[str, str]]:
    """Return a dict of named (or positional) capture groups from *line*.

    If *pattern* has named groups they are used directly.  When *field_names*
    is provided it overrides the positional group names (``group1``, …).
    Returns ``None`` when the pattern does not match.
    """
    m = pattern.search(line)
    if m is None:
        return None

    named = m.groupdict()
    if named:
        return named

    # Positional groups — use supplied names or auto-generate
    groups = m.groups()
    if field_names and len(field_names) == len(groups):
        return dict(zip(field_names, groups))
    return {f"field{i + 1}": v for i, v in enumerate(groups)}


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def export_csv(
    lines: Iterable[str],
    pattern: re.Pattern,
    field_names: Optional[List[str]] = None,
    include_raw: bool = False,
) -> Iterator[str]:
    """Yield CSV rows (including a header) extracted from *lines*.

    Each line is matched against *pattern*; non-matching lines are skipped.
    When *include_raw* is ``True`` the original log line is appended as the
    last column.
    """
    buf = io.StringIO()
    header_written = False

    for raw in lines:
        fields = extract_fields(raw, pattern, field_names)
        if fields is None:
            continue

        if include_raw:
            fields["_raw"] = raw.rstrip("\n")

        if not header_written:
            writer = csv.DictWriter(
                buf,
                fieldnames=list(fields.keys()),
                lineterminator="\n",
            )
            writer.writeheader()
            header_written = True
            yield buf.getvalue()
            buf.truncate(0)
            buf.seek(0)

        writer.writerow(fields)
        yield buf.getvalue()
        buf.truncate(0)
        buf.seek(0)


# ---------------------------------------------------------------------------
# NDJSON export
# ---------------------------------------------------------------------------

def export_ndjson(
    lines: Iterable[str],
    pattern: re.Pattern,
    field_names: Optional[List[str]] = None,
    include_raw: bool = False,
) -> Iterator[str]:
    """Yield one JSON object per line (NDJSON / JSON Lines format).

    Non-matching lines are silently skipped.
    """
    for raw in lines:
        fields = extract_fields(raw, pattern, field_names)
        if fields is None:
            continue
        if include_raw:
            fields["_raw"] = raw.rstrip("\n")
        yield json.dumps(fields, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Plain-text export (passthrough with optional field annotation)
# ---------------------------------------------------------------------------

def export_plain(
    lines: Iterable[str],
    pattern: Optional[re.Pattern] = None,
) -> Iterator[str]:
    """Yield lines unchanged, or only lines that match *pattern*.

    When *pattern* is ``None`` every line is passed through.
    """
    for raw in lines:
        if pattern is None or pattern.search(raw):
            yield raw if raw.endswith("\n") else raw + "\n"


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

_EXPORTERS = {
    "csv": export_csv,
    "ndjson": export_ndjson,
    "plain": export_plain,
}


def export_lines(
    lines: Iterable[str],
    fmt: str,
    pattern: Optional[re.Pattern] = None,
    field_names: Optional[List[str]] = None,
    include_raw: bool = False,
) -> Iterator[str]:
    """Dispatch to the appropriate exporter based on *fmt*.

    Supported formats: ``"csv"``, ``"ndjson"``, ``"plain"``.
    Raises ``ValueError`` for unknown formats.
    """
    fmt = fmt.lower()
    if fmt not in _EXPORTERS:
        raise ValueError(
            f"Unknown export format {fmt!r}. "
            f"Choose from: {', '.join(sorted(_EXPORTERS))}"
        )
    if fmt == "plain":
        yield from export_plain(lines, pattern=pattern)
    else:
        if pattern is None:
            raise ValueError(f"A compiled regex pattern is required for {fmt!r} export.")
        yield from _EXPORTERS[fmt](lines, pattern, field_names=field_names, include_raw=include_raw)
