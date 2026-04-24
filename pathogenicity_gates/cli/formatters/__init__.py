"""Output formatters for the CLI."""
from . import json_fmt, table_fmt, compact_fmt


FORMATTERS = {
    'json': json_fmt,
    'table': table_fmt,
    'compact': compact_fmt,
}


def get_formatter(fmt: str):
    if fmt not in FORMATTERS:
        raise ValueError(f"Unknown format '{fmt}'. Available: {list(FORMATTERS.keys())}")
    return FORMATTERS[fmt]
