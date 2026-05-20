# logslice

Fast log file slicer and filter tool with regex support and time-range queries.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
# Slice logs between two timestamps
logslice app.log --from "2024-01-15 08:00:00" --to "2024-01-15 09:00:00"

# Filter lines matching a regex pattern
logslice app.log --pattern "ERROR|CRITICAL"

# Combine time range and regex filter, output to file
logslice app.log --from "2024-01-15 08:00:00" --to "2024-01-15 09:00:00" \
    --pattern "ERROR" --output errors.log

# Read from stdin
cat app.log | logslice --pattern "timeout"
```

### Python API

```python
from logslice import slice_log

results = slice_log(
    "app.log",
    start="2024-01-15 08:00:00",
    end="2024-01-15 09:00:00",
    pattern=r"ERROR|WARN"
)

for line in results:
    print(line)
```

---

## Features

- ⚡ Fast line-by-line streaming — handles large log files with low memory usage
- 🕐 Time-range queries with flexible timestamp format detection
- 🔍 Full regex pattern filtering
- 📂 Supports plain text and `.gz` compressed log files

---

## License

MIT © 2024 yourname