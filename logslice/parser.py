"""Log line parser with timestamp extraction and regex filtering."""

import re
from datetime import datetime
from typing import Optional

# Common timestamp patterns found in log files
TIMESTAMP_PATTERNS = [
    (r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)', '%Y-%m-%dT%H:%M:%S'),
    (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
    (r'(\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2})', '%b %d %H:%M:%S'),
    (r'(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})', '%d/%b/%Y:%H:%M:%S'),
]


def extract_timestamp(line: str) -> Optional[datetime]:
    """Extract the first recognizable timestamp from a log line."""
    for pattern, fmt in TIMESTAMP_PATTERNS:
        match = re.search(pattern, line)
        if match:
            raw = match.group(1).rstrip('Z').split('+')[0].split('-')[0] if fmt == '%Y-%m-%dT%H:%M:%S' else match.group(1)
            # Normalize ISO 8601
            if 'T' in raw:
                raw = raw.replace('T', ' ')[:19]
                fmt = '%Y-%m-%d %H:%M:%S'
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None


def matches_filter(line: str, pattern: Optional[re.Pattern]) -> bool:
    """Return True if line matches the compiled regex pattern, or if no pattern given."""
    if pattern is None:
        return True
    return bool(pattern.search(line))


def compile_pattern(regex: Optional[str], ignore_case: bool = False) -> Optional[re.Pattern]:
    """Compile a regex string into a Pattern object."""
    if not regex:
        return None
    flags = re.IGNORECASE if ignore_case else 0
    return re.compile(regex, flags)
