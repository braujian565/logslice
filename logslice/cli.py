"""Command-line interface for logslice."""

import sys
from datetime import datetime
from typing import Optional

import click

from logslice.parser import compile_pattern
from logslice.slicer import slice_log

DATETIME_FORMATS = [
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d',
]


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise click.BadParameter(f"Cannot parse datetime: '{value}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")


@click.command()
@click.argument('logfile', type=click.Path(exists=True, readable=True, allow_dash=True))
@click.option('-p', '--pattern', default=None, help='Regex pattern to filter log lines.')
@click.option('-i', '--ignore-case', is_flag=True, default=False, help='Case-insensitive regex matching.')
@click.option('--start', default=None, metavar='DATETIME', help='Include lines at or after this time.')
@click.option('--end', default=None, metavar='DATETIME', help='Include lines at or before this time.')
@click.option('-c', '--count', is_flag=True, default=False, help='Print match count instead of lines.')
def main(logfile, pattern, ignore_case, start, end, count):
    """logslice — Fast log file slicer and filter tool."""
    compiled = compile_pattern(pattern, ignore_case=ignore_case)
    start_dt = parse_datetime(start)
    end_dt = parse_datetime(end)

    opener = click.open_file(logfile, 'r', encoding='utf-8', errors='replace')
    with opener as fh:
        if count:
            from logslice.slicer import count_matches
            total = count_matches(fh, pattern=compiled, start=start_dt, end=end_dt)
            click.echo(total)
        else:
            for line in slice_log(fh, pattern=compiled, start=start_dt, end=end_dt):
                click.echo(line)


if __name__ == '__main__':
    main()
